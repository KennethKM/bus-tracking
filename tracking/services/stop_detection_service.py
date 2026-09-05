from typing import Optional, Dict
from math import isfinite

from ..models import Stop
from .eta_service import calculate_distance


ARRIVAL_THRESHOLD_M = 50.0


def _is_valid_coord(lat, lng) -> bool:
    try:
        if lat is None or lng is None:
            return False
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return False

    if not (isfinite(lat) and isfinite(lng)):
        return False
    if not (-90.0 <= lat <= 90.0):
        return False
    if not (-180.0 <= lng <= 180.0):
        return False
    # Respect existing prototype rule: treat 0,0 as invalid
    if lat == 0.0 and lng == 0.0:
        return False
    return True


def determine_current_and_next_stop(bus) -> Dict[str, Optional[object]]:
    """Read-only determination of current and next stop for a bus.

    Returns dict with keys: current_stop, next_stop, distance_to_current_m,
    distance_to_next_m, candidate_index.

    This function does not write to the database.
    """
    result = {
        "current_stop": None,
        "next_stop": None,
        "distance_to_current_m": None,
        "distance_to_next_m": None,
        "candidate_index": None,
    }

    # Validate GPS
    lat = getattr(bus, 'current_lat', None)
    lng = getattr(bus, 'current_lng', None)
    if not _is_valid_coord(lat, lng):
        return result

    # Ensure route and stops exist
    route = getattr(bus, 'route', None)
    if not route:
        return result

    stops = list(Stop.objects.filter(route=route).order_by('order'))
    if not stops:
        return result

    n = len(stops)

    # compute distances (km -> m)
    distances_m = []
    for s in stops:
        d_km = calculate_distance(lat, lng, s.latitude, s.longitude)
        distances_m.append(d_km * 1000.0)

    # If any stop is within arrival threshold, treat it as current
    within = [(i, d) for i, d in enumerate(distances_m) if d <= ARRIVAL_THRESHOLD_M]
    if within:
        # pick nearest arrived stop
        idx, dval = min(within, key=lambda x: x[1])
        current_idx = idx
        current_stop = stops[current_idx]
        next_stop = stops[current_idx + 1] if (current_idx + 1) < n else None

        result.update({
            "current_stop": current_stop,
            "next_stop": next_stop,
            "distance_to_current_m": round(float(dval), 1),
            "distance_to_next_m": round(float(distances_m[current_idx + 1]), 1) if next_stop is not None else None,
            "candidate_index": int(current_idx),
        })

        return result

    # Not within threshold: use current_stop_index as a route-position hint
    cidx = getattr(bus, 'current_stop_index', None)
    try:
        cidx = int(cidx)
    except Exception:
        cidx = None

    if cidx is not None and 0 <= cidx < n:
        # treat cidx as last arrived stop; next stop is cidx+1 if available
        next_idx = cidx + 1 if (cidx + 1) < n else None
        if next_idx is None:
            # after final stop. For single-stop routes, treat that stop as next
            if n == 1:
                result.update({
                    "current_stop": None,
                    "next_stop": stops[0],
                    "distance_to_current_m": None,
                    "distance_to_next_m": round(float(distances_m[0]), 1),
                    "candidate_index": 0,
                })
                return result

            # otherwise no next stop
            result.update({
                "current_stop": None,
                "next_stop": None,
                "distance_to_current_m": None,
                "distance_to_next_m": None,
                "candidate_index": None,
            })
            return result
        else:
            result.update({
                "current_stop": None,
                "next_stop": stops[next_idx],
                "distance_to_current_m": None,
                "distance_to_next_m": round(float(distances_m[next_idx]), 1),
                "candidate_index": int(next_idx),
            })
            return result

    # Invalid or missing current_stop_index: conservative fallback
    # treat first stop as next (before-first) unless there's evidence otherwise
    result.update({
        "current_stop": None,
        "next_stop": stops[0],
        "distance_to_current_m": None,
        "distance_to_next_m": round(float(distances_m[0]), 1),
        "candidate_index": 0,
    })
    return result
