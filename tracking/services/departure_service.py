from requests.exceptions import RequestException

from .distance_service import get_distance_to_current_stop


def has_departed(bus):

    if bus.current_stop_time is None:
        return False

    try:
        road_distance = get_distance_to_current_stop(bus)

    except RequestException:
        return False

    return (
        road_distance > 30
        and bus.speed > 20
    )