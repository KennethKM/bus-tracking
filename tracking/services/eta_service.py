from math import isfinite

from requests.exceptions import RequestException

from ..models import Bus, StopTime
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


def calculate_waiting_request_eta(waiting_request):
    if waiting_request.status != "WAITING":
        return None

    stop_sequences = list(
        StopTime.objects.filter(
            trip=waiting_request.trip,
            stop=waiting_request.stop,
        ).values_list("stop_sequence", flat=True)
    )
    if not stop_sequences:
        return None

    buses = Bus.objects.filter(
        is_active=True,
        status__in=["IN_TRANSIT", "AT_STOP"],
        current_trip=waiting_request.trip,
        current_lat__isnull=False,
        current_lng__isnull=False,
        current_stop_time__isnull=False,
        current_stop_time__trip=waiting_request.trip,
    ).select_related("current_stop_time")

    shortest_duration = None
    for bus in buses:
        try:
            coordinates_are_valid = (
                isfinite(bus.current_lat)
                and -90 <= bus.current_lat <= 90
                and isfinite(bus.current_lng)
                and -180 <= bus.current_lng <= 180
            )
        except (TypeError, ValueError):
            coordinates_are_valid = False

        if not coordinates_are_valid or not any(
            bus.current_stop_time.stop_sequence <= sequence
            for sequence in stop_sequences
        ):
            continue

        try:
            route = get_road_distance(
                bus.current_lat,
                bus.current_lng,
                waiting_request.stop.stop_lat,
                waiting_request.stop.stop_lon,
            )
            duration = float(route["duration_seconds"])
        except (RequestException, IndexError, KeyError, TypeError, ValueError, OverflowError):
            continue

        if not isfinite(duration) or duration < 0:
            continue

        if shortest_duration is None or duration < shortest_duration:
            shortest_duration = duration

    if shortest_duration is None:
        return None

    return round(shortest_duration / 60, 2)