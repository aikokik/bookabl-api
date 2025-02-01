import asyncio
import logging
import ssl
from collections import defaultdict
from datetime import datetime
from typing import Any, NamedTuple, TypeVar, cast

import aiohttp
from aiohttp import ClientError

from models.availability_models import (
    AvailabilitySlot,
    BookingFormAction,
    BookingProvider,
    BookingTimeSlotMetaData,
)
from models.booking_models import Booking, BookingStatus, BookingUser, Venue
from utils.decorators import log_execution_time

logger = logging.getLogger(__name__)
T = TypeVar("T")


class BookingDetails(NamedTuple):
    link: str
    deposit_required: bool
    details: dict[str, Any]


class TimeSlot(NamedTuple):
    time: str
    action: str


class BookingType(NamedTuple):
    id: str
    name: str


class RequestFailedError(Exception):
    pass


class BookingValidationError(Exception):
    def __init__(self, missing_fields: set[str]) -> None:
        message = f"Missing required booking fields: {', '.join(missing_fields)}"
        super().__init__(message)


class BookingRejectedError(Exception):
    def __init__(self, status: str) -> None:
        message = f"Booking was {status}"
        super().__init__(message)


class DesignMyNightBookingAPI:
    BASE_URL = "https://api.designmynight.com/v4"
    REQUIRED_BOOKING_FIELDS = {
        "venue_id",
        "source",
        "type",
        "first_name",
        "last_name",
        "email",
        "num_people",
        "date",
        "time",
    }

    # Cache configuration
    BOOKING_TYPES_CACHE_TTL = 3600  # 1 hour in seconds
    CACHE_SIZE = 128

    # Request configuration
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 1

    def __init__(self) -> None:
        self.headers = {"Content-Type": "application/json"}
        self.session: aiohttp.ClientSession | None = None
        self._booking_types_cache: dict[str, set[BookingType]] = {}
        self._last_cache_update: dict[str, float] = defaultdict(float)
        # Add SSL context configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED

    async def __aenter__(self) -> "DesignMyNightBookingAPI":
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        )  # TODO(Aidana fix it)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self.session:
            await self.session.close()

    @log_execution_time
    async def _make_request_with_retry(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        if not self.session:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            )

        for attempt in range(self.MAX_RETRIES):
            try:
                kwargs["timeout"] = self.REQUEST_TIMEOUT
                logger.debug(
                    f"Making API request: {method=} {endpoint=} params: {str(kwargs)}, attempt: {attempt + 1}",
                )
                async with self.session.request(
                    method,
                    f"{self.BASE_URL}/{endpoint.lstrip('/')}",
                    headers=self.headers,
                    **kwargs,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    logger.debug(
                        f"API request successful: {response.status}, {endpoint=}, data: {str(data)}",
                    )
                    return cast(dict[str, Any], data)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Request timeout: {endpoint=}, timeout: {self.REQUEST_TIMEOUT}, attempt: {attempt + 1}",
                )

                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Max retries reached for timeout: {endpoint=}")
                    raise
                await asyncio.sleep(2**attempt)
            except ClientError as e:
                logger.warning(
                    f"API request failed: {endpoint=} attempt: {attempt + 1} error: {str(e)}",
                )
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(
                        f"Max retries reached for API request: {endpoint=}, error: {str(e)}",
                    )
                    raise RequestFailedError(f"API request failed: {str(e)}") from e
                await asyncio.sleep(2**attempt)

        raise RequestFailedError("This should never be reached")

    @log_execution_time
    async def get_availability_per_date(
        self, venue_id: str, date: datetime, covers: int
    ) -> list[AvailabilitySlot]:
        booking_types = await self.__get_booking_types(venue_id)
        tasks = []
        for booking_type in booking_types:
            tasks.extend(
                [
                    self.__get_time_slots(venue_id, booking_type.id, covers, date),
                    self.__get_booking_details(venue_id, booking_type.id, covers, date),
                ]
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_slots: list[AvailabilitySlot] = []
        # Process results in pairs (time_slots, booking_details)
        for booking_type, result_index in zip(booking_types, range(0, len(results), 2)):
            time_slots, booking_details = (
                results[result_index],
                results[result_index + 1],
            )
            if isinstance(time_slots, Exception) or not isinstance(
                booking_details, BookingDetails
            ):
                logger.error(
                    f"Failed to get time slots or booking details for {booking_type=}",
                )
                continue  # Skip failed requests

            all_slots.extend(
                self._create_availability_slot(
                    slot, booking_details, date, covers, booking_type
                )
                for slot in (time_slots if isinstance(time_slots, list) else [])
                if isinstance(slot, TimeSlot)
            )

        return sorted(all_slots, key=lambda x: x.timeSlot)  # Sort by time

    def _create_availability_slot(
        self,
        slot: TimeSlot,
        booking_details: BookingDetails,
        date: datetime,
        covers: int,
        booking_type: BookingType,
    ) -> AvailabilitySlot:
        booking_form_action = (
            BookingFormAction.WEBSITE
            if booking_details.deposit_required
            or slot.action in {"enquire", "may_enquire"}
            else BookingFormAction.BOOKING_INJECTION
        )

        return AvailabilitySlot(
            provider=BookingProvider.DESIGN_MY_NIGHT,
            timeSlot=slot.time,
            date=date,
            covers=covers,
            url=booking_details.link,
            maxDuration=90,
            minDuration=45,
            tag=booking_type.name,
            metaData=BookingTimeSlotMetaData(designMyNight=booking_details.details),
            bookingFormAction=booking_form_action,
            requiredDeposit=booking_details.deposit_required,
            dobRequired=False,
        )

    @log_execution_time
    async def create_booking(
        self,
        venue_id: str,
        user: BookingUser,
        availability_slot: AvailabilitySlot,
        covers: int,
    ) -> Booking:
        params = availability_slot.metaData.designMyNight or {}
        params.update(
            {
                "venue_id": venue_id,
                "date": availability_slot.date.strftime("%Y-%m-%d"),
                "time": availability_slot.timeSlot,
                "num_people": covers,
                "source": "partner",
                "first_name": user.firstName,
                "last_name": user.lastName,
                "email": user.email,
                "phone": user.phone,
            }
        )

        missing_fields = self.REQUIRED_BOOKING_FIELDS - params.keys()
        if missing_fields:
            raise BookingValidationError(missing_fields)

        data = await self._make_request_with_retry("POST", "/bookings", json=params)
        return self._create_booking_from_response(data, user)

    @log_execution_time
    async def cancel_booking(self, booking_id: str) -> None:
        logger.info(f"Cancelling booking: {booking_id=}")
        try:
            await self._make_request_with_retry(
                "POST",
                f"/cancel-booking/{booking_id}",
            )
            logger.info(f"Booking cancelled successfully: {booking_id=}")
        except Exception as e:
            logger.error(
                f"Failed to cancel booking: {booking_id=}, error: {str(e)}",
            )
            raise

    def _create_booking_from_response(
        self, data: dict[str, Any], user: BookingUser
    ) -> Booking:
        payload = data["payload"]
        if payload["bookingStatus"] in ["rejected", "lost"]:
            raise BookingRejectedError(status=payload["bookingStatus"])

        booking = payload["booking"]
        return Booking(
            id=booking["_id"],
            dateTime=datetime.combine(
                datetime.fromisoformat(booking["date"]).date(),
                datetime.strptime(booking["time"], "%H:%M").time(),
            ),
            covers=booking["num_people"],
            bookedAt=booking["created_date"],
            status=(
                BookingStatus.COMPLETED
                if payload["bookingStatus"] == "confirmed"
                else BookingStatus.REQUESTED
            ),
            tag=booking["type"]["name"],
            originalEmail=booking["email"],
            venue=Venue(
                id=payload["venue"]["_id"],
                name=payload["venue"]["title"],
                town="London",
            ),
            users=[user],
        )

    @log_execution_time
    async def __get_booking_types(self, venue_id: str) -> set[BookingType]:
        current_time = datetime.now().timestamp()

        # Check cache
        if (
            venue_id in self._booking_types_cache
            and current_time - self._last_cache_update[venue_id]
            < self.BOOKING_TYPES_CACHE_TTL
        ):
            logger.debug(f"Using cached booking types: {venue_id=}")
            return self._booking_types_cache[venue_id]

        logger.debug(f"Fetching booking types: {venue_id=}")
        try:
            data = await self._make_request_with_retry(
                "GET",
                f"/venues/{venue_id}/booking-availability",
                params={
                    "fields": "type",
                    "source": "designmynight",
                    "partner_source": "undefined",
                },
            )

            booking_types = {
                BookingType(id=item["value"]["id"], name=item["value"]["name"])
                for item in data.get("payload", {})
                .get("validation", {})
                .get("type", {})
                .get("suggestedValues", [])
                if isinstance(item, dict) and isinstance(item.get("value"), dict)
            }

            # Update cache
            self._booking_types_cache[venue_id] = booking_types
            self._last_cache_update[venue_id] = current_time

            logger.info(
                f"Successfully fetched booking types: {venue_id=}, {len(booking_types)=}",
            )
            return booking_types

        except Exception as e:
            logger.error(
                f"Failed to fetch booking types: {venue_id=}, error: {str(e)}",
            )
            raise

    async def __get_time_slots(
        self, venue_id: str, booking_type: str, covers: int, date: datetime
    ) -> list[TimeSlot]:
        params = {
            "fields": "time",
            "type": booking_type,
            "num_people": str(covers),  # Pre-convert to string
            "date": date.strftime("%Y-%m-%d"),
        }

        data = await self._make_request_with_retry(
            "GET",
            f"/venues/{venue_id}/booking-availability",
            params=params,
        )

        # Use generator expression for memory efficiency
        return [
            TimeSlot(time=slot["time"], action=slot["action"])
            for slot in (
                data.get("payload", {})
                .get("validation", {})
                .get("time", {})
                .get("suggestedValues", [])
            )
            if slot.get("valid") and slot.get("time") and slot["action"] != "reject"
        ]

    async def __get_booking_details(
        self, venue_id: str, booking_type: str, covers: int, date: datetime
    ) -> BookingDetails:
        params = {
            "fields": "next",
            "type": booking_type,
            "num_people": covers,
            "date": date.strftime("%Y-%m-%d"),
        }
        data = await self._make_request_with_retry(
            "GET",
            f"/venues/{venue_id}/booking-availability",
            params={str(k): str(v) for k, v in params.items()},
        )
        payload = data.get("payload", {})
        return BookingDetails(
            link=payload.get("next", {}).get("web", ""),
            deposit_required=payload.get("depositRequired", False),
            details=payload.get("bookingDetails", {}),
        )
