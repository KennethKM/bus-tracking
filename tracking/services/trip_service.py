from django.db import transaction
from django.shortcuts import get_object_or_404

from tracking.models import (
    Bus,
    Route,
    Trip,
    StopTime,
)




def get_trip_for_route_and_destination(
    route,
    destination,
):
    for candidate_trip in Trip.objects.filter(
    route=route,
    trip_id__endswith="-08:00:00"
    ):

        last_stop_time = (
            StopTime.objects
            .filter(trip=candidate_trip)
            .select_related("stop")
            .order_by("-stop_sequence")
            .first()
        )

        if (
            last_stop_time and
            last_stop_time.stop.stop_name == destination
        ):
            return candidate_trip

    return None





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

    trip = get_trip_for_route_and_destination(
    route,
    destination,
)

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