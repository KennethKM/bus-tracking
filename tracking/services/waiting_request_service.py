from ..models import WaitingRequest, Bus, StopTime
from django.utils import timezone

def get_waiting_count(trip_id, stop_id):

    return WaitingRequest.objects.filter(
        trip_id=trip_id,
        stop_id=stop_id,
        status="WAITING"
    ).count()


def get_route_waiting_overview(registration_number):

    bus = Bus.objects.select_related(
        "current_trip__route"
    ).get(
        registration_number=registration_number
    )

    if bus.current_trip is None:
        return {
            "registration_number": bus.registration_number,
            "trip_id": None,
            "route_id": None,
            "route": None,
            "stops": []
        }

    trip = bus.current_trip
    route = trip.route

    stop_times = (
        StopTime.objects
        .filter(trip=trip)
        .select_related("stop")
        .order_by("stop_sequence")
    )

    results = []

    for stop_time in stop_times:

        stop = stop_time.stop

        waiting_count = WaitingRequest.objects.filter(
            trip=trip,
            stop=stop,
            status="WAITING"
        ).count()

        results.append({
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "stop_sequence": stop_time.stop_sequence,
            "waiting_count": waiting_count
        })

    return {
        "registration_number": bus.registration_number,
        "trip_id": trip.trip_id,
        "route_id": route.route_id,
        "route": route.route_long_name,
        "stops": results
    }



def mark_as_boarded(waiting_request_id, passenger):
    waiting_request = WaitingRequest.objects.get(
        id=waiting_request_id,
        passenger=passenger,
        status="WAITING"
    )

    waiting_request.status = "ON_BOARD"
    waiting_request.save(update_fields=["status"])

    return waiting_request


def cancel_waiting_request(waiting_request_id, passenger):
    waiting_request = WaitingRequest.objects.get(
        id=waiting_request_id,
        passenger=passenger,
        status="WAITING"
    )

    waiting_request.status = "CANCELLED"
    waiting_request.deactivated_at = timezone.now()

    waiting_request.save(
        update_fields=["status", "deactivated_at"]
    )

    return waiting_request


def complete_waiting_request(waiting_request_id, passenger):
    waiting_request = WaitingRequest.objects.get(
        id=waiting_request_id,
        passenger=passenger,
        status="ON_BOARD"
    )

    waiting_request.status = "COMPLETED"
    waiting_request.deactivated_at = timezone.now()

    waiting_request.save(
        update_fields=["status", "deactivated_at"]
    )

    return waiting_request


def expire_waiting_request(waiting_request_id):
    waiting_request = WaitingRequest.objects.get(
        id=waiting_request_id,
        status="WAITING"
    )

    waiting_request.status = "EXPIRED"
    waiting_request.deactivated_at = timezone.now()

    waiting_request.save(
        update_fields=["status", "deactivated_at"]
    )

    return waiting_request