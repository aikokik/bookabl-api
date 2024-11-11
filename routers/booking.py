from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Path, Query

from booking_providers.design_my_night import DesignMyNightBookingAPI
from docs.docs import AVAILABILITY_DOCS, CREATE_BOOKING_DOCS, PRE_CONFIRMATION_DOCS
from models.availability_models import (
    AvailabilityResponse,
    AvailabilitySlot,
    BookingFormAction,
    BookingProvider,
    BookingTimeSlotMetaData,
)
from models.booking_models import (
    Booking,
    BookingStatus,
    BookingUser,
    Partner,
    PreConfirmationResponse,
    Venue,
)

router = APIRouter()


@router.get(
    "/venues/{venue_id}/availability",
    response_model=AvailabilityResponse,
    description=AVAILABILITY_DOCS["description"],
)
async def get_availability_per_range(
    venue_id: str,
    start: datetime = Query(..., description="Start datetime in UTC format"),
    end: datetime = Query(..., description="End datetime in UTC format"),
    covers: int = Query(..., description="Number of guests"),
) -> AvailabilityResponse:
    # Mock response for demonstration
    return AvailabilityResponse(
        success=True,
        cached=False,
        slots=[
            AvailabilitySlot(
                provider=BookingProvider.SEVEN_ROOMS,
                timeSlot="18:00",
                date=start,
                covers=covers,
                url="https://www.sevenrooms.com/explore/example/reservations",
                maxDuration=150,
                minDuration=90,
                metaData=BookingTimeSlotMetaData(
                    sevenRooms={"type": "request", "access_persistent_id": "example-id"}
                ),
                dobRequired=False,
                bookingFormAction=BookingFormAction.WEBSITE,
            )
        ],
    )


@router.get(
    "/venues/{venue_id}/availability/{date}",
    response_model=AvailabilityResponse,
    description=AVAILABILITY_DOCS["single_date_description"],
)
async def get_availability_per_date(
    venue_id: str,
    date: datetime = Path(..., description="Date in YYYY-MM-DD format"),
    covers: int = Query(..., description="Number of guests"),
) -> AvailabilityResponse:
    async with DesignMyNightBookingAPI() as api:
        availability = await api.get_availability_per_date(venue_id, date, covers)
        return AvailabilityResponse(success=True, cached=False, slots=availability)


@router.post(
    "/venues/{venue_id}/pre-confirmation",
    response_model=PreConfirmationResponse,
    description=PRE_CONFIRMATION_DOCS["description"],
)
async def get_pre_confirmation(
    venue_id: str = Path(..., description="The ID of the venue"),
    availability_slot: AvailabilitySlot = Body(
        ..., description="The selected availability slot"
    ),
) -> PreConfirmationResponse:
    return PreConfirmationResponse(
        notes="We have a 5 minute grace period. Please call us if you are running later.",
        bookingUrl=(
            availability_slot.url
            if availability_slot.url
            else "https://booking.com/my-booking-form"
        ),
    )


@router.post(
    "/bookings",
    response_model=Booking,
    description=CREATE_BOOKING_DOCS["description"],
)
async def create_booking(
    venue_id: str = Body(..., description="The ID of the venue"),
    user: BookingUser = Body(..., description="The user making the booking"),
    availability_slot: AvailabilitySlot = Body(
        ..., description="The selected availability slot"
    ),
    covers: int = Body(
        ..., description="Number of guests"
    ),  # TODO: if availability already provided , do we need this at all
) -> Booking:
    async with DesignMyNightBookingAPI() as api:
        booking = await api.create_booking(venue_id, user, availability_slot, covers)
        return booking


@router.get(
    "/bookings",
    response_model=list[Booking],
    description="List all bookings",
)
async def list_bookings(
    user: BookingUser = Query(..., description="The user whose bookings to fetch"),
    venue_id: str = Query(None, description="Optional venue ID to filter bookings"),
    upcoming_only: bool = Query(
        False, description="If true, only returns future bookings"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of bookings to return"
    ),
) -> list[Booking]:
    """List the bookings made on your platform."""
    # Your booking list logic here
    return []


@router.delete(
    "/bookings/{booking_id}",
    description="Cancel a booking",
)
async def cancel_booking(
    booking_id: str = Path(..., description="The ID of the booking to cancel"),
) -> None:
    return None
