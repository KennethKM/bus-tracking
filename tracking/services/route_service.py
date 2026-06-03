from ..models import Bus, Passenger
from .eta_service import calculate_distance, calculate_eta


def get_active_buses():
    return Bus.objects.filter(is_active=True)


def get_nearby_buses(passenger):

    buses = get_active_buses()

    results = []

    for bus in buses:

        distance = calculate_distance(
            passenger.latitude,
            passenger.longitude,
            bus.current_lat,
            bus.current_lng
        )

        eta_minutes = calculate_eta(
            distance,
            bus.speed
        )

        results.append({
            "bus_id": bus.id,
            "distance_km": round(distance, 2),
            "estimated_wait_time": f"{eta_minutes} minutes",
            "eta_minutes": eta_minutes
        })

    results.sort(key=lambda x: x["eta_minutes"])

    for bus in results:
        bus.pop("eta_minutes")

    return results


def get_nearby_passengers(bus):

    active_passengers = Passenger.objects.filter(
        is_active=True
    )

    nearby = []

    for passenger in active_passengers:

        distance = calculate_distance(
            bus.current_lat,
            bus.current_lng,
            passenger.latitude,
            passenger.longitude
        )

        if distance <= 2:

            nearby.append({
                "id": passenger.id,
                "name": passenger.name,
                "distance_km": round(distance, 2)
            })

    return nearby