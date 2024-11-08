from datetime import datetime
from typing import Any, List, NamedTuple

import requests

from models.availability_models import (
    AvailabilitySlot,
    BookingFormAction,
    BookingProvider,
    BookingTimeSlotMetaData,
)
from models.booking_models import Booking, BookingStatus, BookingUser, Partner, Venue


class BookingDetails(NamedTuple):
    link: str
    deposit_required: bool
    details: dict[str, Any]


class TimeSlot(NamedTuple):
    time: str
    action: str


class DesignMyNightBookingAPI:
    def __init__(self) -> None:
        self.base_url = "https://api.designmynight.com/v4"
        # You'll need to add your API key if required
        self.headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer YOUR_API_KEY"  # If needed
        }

    def get_availability_per_date(
        self, venue_id: str, date: datetime, covers: int
    ) -> List[AvailabilitySlot]:
        booking_types = self.__get_booking_types(venue_id)
        available_slots = []
        for booking_type in booking_types:
            time_slots = self.__get_time_slots(venue_id, booking_type, covers, date)
            booking_details = self.__get_booking_details(
                venue_id, booking_type, covers, date
            )
            for slot in time_slots:
                booking_form_action = (
                    BookingFormAction.WEBSITE
                    if booking_details.deposit_required
                    or slot.action in {"enquire", "may_enquire"}
                    else BookingFormAction.BOOKING_INJECTION
                )
                available_slots.append(
                    AvailabilitySlot(
                        provider=BookingProvider.DESIGN_MY_NIGHT,
                        timeSlot=slot.time,
                        date=date,
                        covers=covers,
                        url=booking_details.link,
                        maxDuration=90,
                        minDuration=45,
                        tag=booking_type,
                        metaData=BookingTimeSlotMetaData(
                            designMyNight={
                                **booking_details.details,
                            }
                        ),
                        bookingFormAction=booking_form_action,
                        requiredDeposit=booking_details.deposit_required,
                        dobRequired=False,
                    )
                )

        return available_slots

    def create_booking(
        self,
        venue_id: str,
        user: BookingUser,
        availability_slot: AvailabilitySlot,
        covers: int,
    ) -> Booking:
        url = f"{self.base_url}/bookings"
        params = {
            **(availability_slot.metaData.designMyNight or {}),
            "source": "designmynight",
            "first_name": user.firstName,
            "last_name": user.lastName,
            "email": user.email,
            "phone": user.phone,
        }
        if not self.__validate_required_booking_details(params):
            raise ValueError("Missing required booking details")

        response = requests.post(url, json=params, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        booking_status = (
            BookingStatus.COMPLETED
            if data["payload"]["bookingStatus"] == "complete"
            else BookingStatus.REQUESTED
        )
        venue_name = data["payload"]["venue"]["title"]
        booking = data["payload"]["booking"]
        return Booking(
            id=booking["id"],
            dateTime=datetime.combine(
                datetime.fromisoformat(booking["date"]).date(),
                datetime.strptime(booking["time"], "%H:%M").time(),
            ),
            covers=booking["num_people"],
            bookedAt=booking["created_date"],
            status=booking_status,
            tag=booking["type"]["name"],
            originalEmail=booking["email"],
            venue=Venue(id=booking["venue_id"], name=venue_name, town="London"),
            users=[user],
            partner=Partner(id=booking["created_by"], name=booking["reference"]),
        )

    def __validate_required_booking_details(self, details: dict[str, Any]) -> bool:
        required_fields = [
            "venue_id",
            "source",
            "type",
            "first_name",
            "last_name",
            "email",
            "num_people",
            "date",
            "time",
        ]
        return all(field in details for field in required_fields)

    def __get_booking_types(self, venue_id: str) -> set[str]:
        url = f"{self.base_url}/venues/{venue_id}/booking-availability"
        params = {
            "fields": "type",
            "source": "designmynight",
            "partner_source": "undefined",
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        type_ids = {
            item["value"]["id"]
            for item in data.get("payload", {})
            .get("validation", {})
            .get("type", {})
            .get("suggestedValues", [])
        }
        return type_ids

    def __get_time_slots(
        self, venue_id: str, booking_type: str, covers: int, date: datetime
    ) -> list[TimeSlot]:
        url = f"{self.base_url}/venues/{venue_id}/booking-availability"
        params = {
            "fields": "time",
            "type": booking_type,
            "num_people": covers,
            "date": date.strftime("%Y-%m-%d"),
        }
        response = requests.get(
            url,
            headers=self.headers,
            params={str(k): str(v) for k, v in params.items()},
        )
        response.raise_for_status()
        data = response.json()
        suggested_time_slots = (
            data.get("payload", {})
            .get("validation", {})
            .get("time", {})
            .get("suggestedValues", [])
        )
        time_slots = [
            TimeSlot(time=slot["time"], action=slot["action"])
            for slot in suggested_time_slots
            if slot.get("valid") and slot["time"] and slot["action"] != "reject"
        ]
        return time_slots

    def __get_booking_details(
        self, venue_id: str, booking_type: str, covers: int, date: datetime
    ) -> BookingDetails:
        default_booking_url = ""
        url = f"{self.base_url}/venues/{venue_id}/booking-availability"
        params = {
            "fields": "next",
            "type": booking_type,
            "num_people": covers,
            "date": date.strftime("%Y-%m-%d"),
        }
        response = requests.get(
            url,
            headers=self.headers,
            params={str(k): str(v) for k, v in params.items()},
        )
        response.raise_for_status()
        data = response.json()
        booking_url = (
            data.get("payload", {}).get("next", {}).get("web", default_booking_url)
            or default_booking_url
        )
        deposit_required = data.get("payload", {}).get("depositRequired", False)
        booking_details = data.get("payload", {}).get("bookingDetails", {})
        return BookingDetails(
            link=booking_url, deposit_required=deposit_required, details=booking_details
        )
