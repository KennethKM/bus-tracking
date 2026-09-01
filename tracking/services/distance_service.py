import requests


OSRM_URL = "http://localhost:5000"


def get_road_distance(
    start_lat,
    start_lng,
    end_lat,
    end_lng
):
    url = (
        f"{OSRM_URL}/route/v1/driving/"
        f"{start_lng},{start_lat};"
        f"{end_lng},{end_lat}"
        "?overview=false"
    )

    response = requests.get(url)

    response.raise_for_status()

    data = response.json()

    route = data["routes"][0]

    return {
        "distance_meters": route["distance"],
        "duration_seconds": route["duration"],
    }


def get_distance_to_current_stop(bus):

    if bus.current_stop_time is None:
        return None

    stop = bus.current_stop_time.stop

    result = get_road_distance(
        bus.current_lat,
        bus.current_lng,
        stop.stop_lat,
        stop.stop_lon,
    )

    return result["distance_meters"]