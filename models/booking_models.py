# ruff: noqa: N815
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class BookingStatus(StrEnum):
    COMPLETED = "completed"
    NO_SHOW = "noShow"
    CANCELLED = "cancelled"
    REQUESTED = "requested"
    PENDING_PAYMENT = "pendingPayment"
    UPCOMING = "upcoming"


class Currency(StrEnum):
    USD = "USD"
    GBP = "GBP"
    EUR = "EUR"


class Deposit(BaseModel):
    amountUnits: int
    amountPer: str = "guest"  # Fixed as 'guest' per docs
    currency: Currency
    terms: str | None = None


class Partner(BaseModel):
    id: str
    name: str
    logoUrl: str | None = None


class Venue(BaseModel):
    id: str
    name: str
    town: str | None = None


class BookingUser(BaseModel):
    id: str
    isOwner: bool
    email: str | None = None
    phone: str | None = None
    firstName: str | None = None
    lastName: str | None = None


class Booking(BaseModel):
    id: str
    dateTime: datetime
    covers: int
    bookedAt: datetime
    status: BookingStatus
    tag: str | None = None
    originalEmail: str
    venue: Venue
    users: list[BookingUser]
    partner: Partner
    deposit: Deposit | None = None


class PreConfirmationResponse(BaseModel):
    notes: str
    bookingUrl: str | None = None
