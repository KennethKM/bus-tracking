from ..models import WaitingRequest
from ..models import WaitingRequest, Bus, Stop

def get_waiting_count(route_id, stop_id):

    waiting_count = WaitingRequest.objects.filter(
        route_id=route_id,
        stop_id=stop_id,
        status="WAITING"
    ).count()

    return waiting_count




def get_route_waiting_overview(bus_id):

    bus = Bus.objects.get(id=bus_id)

    route = bus.route

    stops = Stop.objects.filter(
        route=route
    ).order_by("order")

    results = []

    for stop in stops:

        waiting_count = WaitingRequest.objects.filter(
            route=route,
            stop=stop,
            status="WAITING"
        ).count()

        results.append({
            "stop": stop.name,
            "waiting_count": waiting_count
        })

    return {
        "route": route.name,
        "stops": results
    }


def mark_as_boarded(waiting_request_id):

    waiting_request = WaitingRequest.objects.get(
        id=waiting_request_id
    )

    waiting_request.status = "ON_BOARD"

    waiting_request.save()

    passenger = waiting_request.passenger

    passenger.is_active = False

    passenger.save()

    return waiting_request