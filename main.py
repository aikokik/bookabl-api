from datetime import datetime

from fastapi import APIRouter, Query

from models.availability_models import (
    AvailabilityResponse,
    AvailabilitySlot,
    BookingFormAction,
    BookingProvider,
    BookingTimeSlotMetaData,
)

router = APIRouter()


@router.get(
    "/venues/{venue_id}/availability",
    response_model=AvailabilityResponse,
    description="Fetches availability slots for a venue. Pulls live availability from venue's ERB.",
)
async def get_availability(
    venue_id: str,
    dateTime: datetime = Query(..., description="UTC format datetime"),
    covers: int = Query(..., description="Number of guests"),
) -> AvailabilityResponse:
    """
    Fetches availability slots for a venue. Pulls live availability from venue's
    Electronic Reservation Book (ERB). If a venue works with multiple ERBs,
    then availability is automatically aggregated.

    Args:
        venue_id: The ID of the venue
        dateTime: UTC format datetime for the booking
        covers: Number of guests

    Returns:
        AvailabilityResponse containing available slots
    """
    # Mock response for demonstration
    return AvailabilityResponse(
        success=True,
        cached=False,
        slots=[
            AvailabilitySlot(
                provider=BookingProvider.SEVEN_ROOMS,
                timeSlot="18:00",
                date=dateTime,
                url="https://www.sevenrooms.com/explore/example/reservations",
                maxDuration=150,
                metaData=BookingTimeSlotMetaData(
                    sevenRooms={"type": "request", "access_persistent_id": "example-id"}
                ),
                dobRequired=False,
                bookingFormAction=BookingFormAction.WEBSITE,
            )
        ],
    )
