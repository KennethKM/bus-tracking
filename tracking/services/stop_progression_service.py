from typing import Optional

from ..models import Stop
from .stop_detection_service import determine_current_and_next_stop, ARRIVAL_THRESHOLD_M


def advance_bus_stop_progress(bus) -> Optional[object]:
    """Advance bus.current_stop_index by one when the next stop is within arrival threshold.

    Returns the bus (unchanged or updated). Only writes `current_stop_index` when it needs to advance.
    """
    if not bus:
        return bus

    # Only advance for active buses
    if not getattr(bus, 'is_active', False):
        return bus

    route = getattr(bus, 'route', None)
    if not route:
        return bus

    stops = list(Stop.objects.filter(route=route).order_by('order'))
    if not stops:
        return bus

    # Use the read-only detection service
    det = determine_current_and_next_stop(bus) or {}
    next_stop = det.get('next_stop')
    dist_to_next = det.get('distance_to_next_m')
    current_stop = det.get('current_stop')
    dist_to_current = det.get('distance_to_current_m')

    # current index safety
    try:
        curr_idx = int(getattr(bus, 'current_stop_index', 0))
    except Exception:
        curr_idx = 0

    # Helper: find index of a stop in ordered stops
    def find_index(stop_obj):
        if not stop_obj:
            return None
        for i, s in enumerate(stops):
            if s.id == stop_obj.id:
                return i
        return None

    # Prefer checking next_stop distance if present
    next_idx = find_index(next_stop)
    if next_idx is not None:
        # only allow single-step forward
        if next_idx == curr_idx + 1:
            try:
                d = float(dist_to_next)
            except Exception:
                return bus
            if d <= ARRIVAL_THRESHOLD_M:
                bus.current_stop_index = next_idx
                bus.save(update_fields=['current_stop_index'])
        return bus

    # If detection reported current_stop (i.e., bus is at a stop), and that
    # stop is the next logical stop, advance as well.
    cur_idx = find_index(current_stop)
    if cur_idx is not None and cur_idx == curr_idx + 1:
        try:
            dcur = float(dist_to_current)
        except Exception:
            return bus
        if dcur <= ARRIVAL_THRESHOLD_M:
            bus.current_stop_index = cur_idx
            bus.save(update_fields=['current_stop_index'])

    return bus
