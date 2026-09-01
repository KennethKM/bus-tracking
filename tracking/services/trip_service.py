from django.db import transaction
from django.shortcuts import get_object_or_404

from tracking.models import (
    Bus,
    Route,
    Trip,
    StopTime,
)


def start_trip(
    registration_number,
    route_id,
    destination,
):
    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    route = get_object_or_404(
        Route,
        route_id=route_id
    )

    trip = None

    for candidate_trip in Trip.objects.filter(route=route):

        last_stop_time = (
            StopTime.objects
            .filter(trip=candidate_trip)
            .order_by("-stop_sequence")
            .first()
        )

        if (
            last_stop_time and
            last_stop_time.stop.stop_name == destination
        ):
            trip = candidate_trip
            break

    if trip is None:
        raise ValueError(
            "No trip ends at the selected destination."
        )

    first_stop_time = (
        StopTime.objects
        .filter(trip=trip)
        .order_by("stop_sequence")
        .first()
        )

    if first_stop_time is None:
        raise ValueError(
            "Selected trip has no stop times."
        )

    with transaction.atomic():

        bus.current_trip = trip
        bus.current_stop_time = first_stop_time

        bus.status = "IDLE"
        bus.is_active = True

        bus.save()

    return bus