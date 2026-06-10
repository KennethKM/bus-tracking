from math import radians, cos, sin, asin, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):

    # approximate radius of earth in km
    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    return R * c


def calculate_eta(distance_km, speed_kmh):

    if speed_kmh <= 0:
        speed_kmh = 30

    return round((distance_km / speed_kmh) * 60)

def get_bus_eta(bus, passenger):

    distance = calculate_distance(
        bus.current_lat,
        bus.current_lng,
        passenger.latitude,
        passenger.longitude
    )

    if bus.speed <= 0:

        return {
            "error": "Bus is not moving"
        }

    eta_minutes = calculate_eta(
        distance,
        bus.speed
    )

    return {

        "bus_id": bus.id,

        "passenger_id": passenger.id,

        "distance_km": round(distance, 2),

        "speed_kmh": bus.speed,

        "estimated_wait_time": f"{eta_minutes} minutes"
    }
    
import math

def calculate_eta(bus, stop):

    distance = math.sqrt(
        (bus.current_lat - stop.latitude) ** 2 +
        (bus.current_lng - stop.longitude) ** 2
    )

    # Convert degrees to KM
    distance_km = distance * 111

    if bus.speed <= 0:
        return 0

    eta = (distance_km / bus.speed) * 60

    return round(eta) 