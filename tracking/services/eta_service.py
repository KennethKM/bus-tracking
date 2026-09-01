from .distance_service import get_road_distance


def calculate_eta(bus, stop):

    result = get_road_distance(
        bus.current_lat,
        bus.current_lng,
        stop.stop_lat,
        stop.stop_lon
    )

    eta_minutes = result["duration_seconds"] / 60

    return round(eta_minutes, 2)