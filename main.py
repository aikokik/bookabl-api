from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import booking
from utils.logging_config import setup_logging

setup_logging(log_level="DEBUG", log_dir="logs", app_name="booking_api")
app = FastAPI(
    title="Booking API",
    description="API for managing venue bookings and availability",
    version="1.0.0",
)

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(booking.router, prefix="/api/v1", tags=["bookings"])
# some comment to check github actions
