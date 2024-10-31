# ruff: noqa: N815
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BookingProvider(StrEnum):
    DESIGN_MY_NIGHT = "designMyNight"
    OPEN_TABLE = "openTable"
    RESY = "resy"
    SEVEN_ROOMS = "sevenRooms"
    RES_DIARY = "resDiary"
    THE_FORK = "theFork"
    QUANDOO = "quandoo"
    TOCK = "tock"
    MOCK = "mock_booking_provider"


class BookingFormAction(StrEnum):
    WEBSITE = "website"
    BOOKING_INJECTION = "booking_injection"
    REQUEST_BOOKING = "request_booking"


class RequiredDeposit(BaseModel):
    amount_units: int
    amount_per: str = "guest"
    currency: str
    terms: str | None = None


class BookingTimeSlotMetaData(BaseModel):
    sevenRooms: dict | None = None
    openTable: dict | None = None
    resy: dict | None = None
    designMyNight: dict | None = None
    resDiary: dict | None = None
    theFork: dict | None = None
    quandoo: dict | None = None
    tock: dict | None = None


class AvailabilitySlot(BaseModel):
    provider: BookingProvider
    timeSlot: str = Field(..., description="The time of the booking (in HH:mm format)")
    date: datetime
    url: str
    maxDuration: int | None = Field(None, description="Maximum duration in seconds")
    minDuration: int | None = None
    tag: str | None = None
    metaData: BookingTimeSlotMetaData | None = None
    bookingFormAction: BookingFormAction
    requiredDeposit: RequiredDeposit | None = None
    dobRequired: bool = False


class AvailabilityResponse(BaseModel):
    success: bool
    cached: bool
    slots: list[AvailabilitySlot]
