from tracking.models import StopTime
from tracking.services.departure_service import has_departed


def update_next_stop(bus):

    if bus.current_trip is None:
        return

    if bus.current_stop_time is None:
        return

    if not has_departed(bus):
        return

    next_stop_time = (
        StopTime.objects
        .filter(
            trip=bus.current_trip,
            stop_sequence__gt=bus.current_stop_time.stop_sequence
        )
        .order_by("stop_sequence")
        .first()
    )

    if next_stop_time is None:
        return

    bus.current_stop_time = next_stop_time
    bus.save()