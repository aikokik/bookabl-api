AVAILABILITY_DOCS = {
    "description": """
        Fetches availability slots for a venue. Pulls live availability from venue's
        Electronic Reservation Book (ERB). If a venue works with multiple ERBs,
        then availability is automatically aggregated.

        Endpoint: /venues/{venue_id}/availability?start=2024-03-20T18:00:00Z&end=2024-03-20T22:00:00Z&covers=2

        Args:
            venue_id: The ID of the venue
            start: Start datetime in UTC format
            end: End datetime in UTC format
            covers: Number of guests

        Returns:
            AvailabilityResponse containing available slots
    """,
    "response_description": """
        Example Response:
        {
            "success": true,
            "cached": false,
            "slots": [
                {
                    "provider": "sevenRooms",
                    "timeSlot": "18:00",
                    "date": "2024-10-04T17:00:00.000Z",
                    "url": "https://www.sevenrooms.com/explore/casafofo/reservations/create/search?date=2024-10-04&party_size=2&start_time=18:00",
                    "maxDuration": 150,
                    "metaData": {
                        "sevenRooms": {
                            "type": "request",
                            "access_persistent_id": (
                                "ahNzfnNldmVucm9vbXMtc2VjdXJlchwLEg9uaWdodGxvb3Bf"
                                "VmVudWUYgID2rdOtoAgM-1720795994.624218-0.5917197656369396"
                            )
                        }
                    },
                    "dobRequired": false,
                    "bookingFormAction": "website"
                },
                {
                    "provider": "sevenRooms",
                    "timeSlot": "18:30",
                    "date": "2024-10-04T17:30:00.000Z",
                    "url": "https://www.sevenrooms.com/explore/casafofo/reservations/create/search?date=2024-10-04&party_size=2&start_time=18:30",
                    "maxDuration": 150,
                    "metaData": {
                        "sevenRooms": {
                            "type": "book",
                            "access_persistent_id": (
                                "ahNzfnNldmVucm9vbXMtc2VjdXJlchwLEg9uaWdodGxvb3BfVmVudWUYgID2rdOtoAgM"
                                "-1720795994.624218-0.5917197656369396"
                            )
                        }
                    },
                    "dobRequired": false,
                    "bookingFormAction": "website"
                }
            ]
        }
    """,
}

PRE_CONFIRMATION_DOCS = {
    "description": """
        Fetches pre-confirmation information for a booking.
        Endpoint: /venues/{venue_id}/pre-confirmation

        Args:
            venue_id: The ID of the venue
            availability_slot: The selected time slot from availability search
    """,
    "response_description": """
        Example Response:
        {
            "notes": "We have a 5 minute grace period. Please call us if you are running later.",
            "url": "https://www.sevenrooms.com/explore/casafofo/reservations/create/search?date=2024-10-04&party_size=2&start_time=18:00"
        }
    """,
}

CREATE_BOOKING_DOCS = {
    "description": """
        Creates a booking at a venue for a specified availability slot.
        Endpoint: /venues/{venue_id}/book

        Args:
            venue_id: The ID of the venue
            user: The user making the booking
            availability_slot: The selected time slot from availability search
            covers: Number of guests
    """,
    "response_description": """
        Example Response:
        {
            "id": "1234567890"
        }
    """,
}
