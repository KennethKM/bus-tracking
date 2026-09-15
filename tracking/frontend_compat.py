"""Small data-shape helpers for the integration frontend contract."""


def normalize_route_search(payload):
    """Convert route search records into the UI's internal option shape."""
    return [
        {
            "id": item.get("route_id"),
            "label": item.get("route_long_name"),
        }
        for item in (payload or [])
    ]


def normalize_route_destinations(payload):
    """Return destination values from integration route destination responses."""
    return [item.get("destination") for item in (payload or []) if item.get("destination")]


def normalize_trip_stops(payload):
    """Convert the integration trip-stop response to the UI's internal shape."""
    stops = payload.get("stops", []) if isinstance(payload, dict) else []
    return {
        "tripId": payload.get("trip_id"),
        "routeId": payload.get("route_id"),
        "destination": payload.get("destination"),
        "stops": [
            {
                "id": stop.get("stop_id"),
                "name": stop.get("stop_name"),
                "stop_sequence": stop.get("stop_sequence"),
            }
            for stop in stops
        ],
    }


def normalize_bus_payload(payload):
    """Return only bus fields exposed by the integration Bus serializer."""
    if not isinstance(payload, dict):
        return {}

    fields = (
        "id",
        "registration_number",
        "status",
        "current_trip",
        "current_stop_time",
        "current_lat",
        "current_lng",
        "speed",
        "last_updated",
        "is_active",
    )
    return {field: payload.get(field) for field in fields if field in payload}
