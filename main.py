from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Path, Query

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
    # Single date logic here
    # Mock response for demonstration
    return AvailabilityResponse(
        success=True,
        cached=False,
        slots=[
            AvailabilitySlot(
                provider=BookingProvider.SEVEN_ROOMS,
                timeSlot="18:00",
                date=date,
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
    covers: int = Body(..., description="Number of guests"),
) -> Booking:
    try:
        # Mock response for demonstration
        return Booking(
            id="booking_123",
            dateTime=availability_slot.date,
            covers=covers,
            bookedAt=datetime.now(),
            status=BookingStatus.REQUESTED,
            originalEmail=user.email or "",  # Ensure non-null string
            venue=Venue(id=venue_id, name="Example Venue"),
            users=[user],
            partner=Partner(id="partner_123", name="Example Partner"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create booking: {str(e)}"
        )


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
