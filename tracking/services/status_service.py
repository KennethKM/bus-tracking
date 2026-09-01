from requests.exceptions import RequestException

from .distance_service import get_distance_to_current_stop


def get_bus_status(bus):

    if bus.current_stop_time is None:
        return "IN_TRANSIT"

    try:
        road_distance = get_distance_to_current_stop(bus)

    except RequestException:
        return "IN_TRANSIT"

    if (
        road_distance <= 30
        and bus.speed <= 20
    ):
        return "AT_STOP"

    return "IN_TRANSIT"