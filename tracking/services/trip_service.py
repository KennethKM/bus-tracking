from ..models import Driver, RouteRequest


def complete_approved_request_for_finished_trip(driver_id, bus):
    """Complete the specific APPROVED RouteRequest for a finished trip.

    Matches ONLY driver + bus + bus.route with status APPROVED.
    Idempotent: COMPLETED/PENDING/REJECTED rows are never changed.
    Returns the completed RouteRequest or None.
    """
    if bus is None or getattr(bus, 'route_id', None) is None:
        return None
    try:
        driver_id = int(driver_id)
    except (TypeError, ValueError):
        return None
    candidate = (
        RouteRequest.objects.filter(
            driver_id=driver_id,
            bus_id=bus.id,
            route_id=bus.route_id,
            status=RouteRequest.STATUS_APPROVED,
        )
        .order_by('-approved_at', '-id')
        .first()
    )
    if candidate is None:
        return None
    candidate.status = RouteRequest.STATUS_COMPLETED
    candidate.save(update_fields=['status'])
    return candidate


def start_trip_for_driver(driver_id):
    """Mark the assigned bus for a driver as active (start trip).

    Also resets stale stop progress so a new trip always starts at 0.

    Raises Driver.DoesNotExist if driver missing.
    Raises ValueError if driver has no assigned bus.
    Returns dict with driver_id, bus_id, is_active, current_stop_index,
    and optional route info.
    """
    driver = Driver.objects.get(id=driver_id)

    if not driver.assigned_bus:
        raise ValueError("Driver has no assigned bus")

    bus = driver.assigned_bus
    bus.is_active = True
    bus.current_stop_index = 0
    bus.save(update_fields=['is_active', 'current_stop_index'])

    route = None
    try:
        r = bus.route
        if r:
            route = {
                "id": r.id,
                "name": r.name,
                "origin": r.origin,
                "destination": r.destination,
            }
    except Exception:
        route = None

    return {
        "driver_id": driver.id,
        "bus_id": bus.id,
        "is_active": bus.is_active,
        "current_stop_index": bus.current_stop_index,
        "route": route,
    }


def stop_trip_for_driver(driver_id):
    """Mark the assigned bus for a driver as inactive (stop trip).

    Same error semantics as start_trip_for_driver.
    """
    driver = Driver.objects.get(id=driver_id)

    if not driver.assigned_bus:
        raise ValueError("Driver has no assigned bus")

    bus = driver.assigned_bus
    bus.is_active = False
    bus.save()

    route = None
    try:
        r = bus.route
        if r:
            route = {
                "id": r.id,
                "name": r.name,
                "origin": r.origin,
                "destination": r.destination,
            }
    except Exception:
        route = None

    return {
        "driver_id": driver.id,
        "bus_id": bus.id,
        "is_active": bus.is_active,
        "current_stop_index": bus.current_stop_index,
        "route": route,
    }


def finish_trip_at_shape_end(driver_id):
    """Finish trip when simulation reaches its selected shape end.

    Publishes nothing; caller must already have saved the final coordinate.
    Completes ONLY the matching APPROVED request, then deactivates bus.
    After completion, clears Bus.route so the bus becomes route-free until a
    new route is approved.
    Idempotent.
    """
    driver = Driver.objects.get(id=driver_id)
    if not driver.assigned_bus:
        raise ValueError("Driver has no assigned bus")
    bus = driver.assigned_bus
    completed = complete_approved_request_for_finished_trip(driver.id, bus)
    bus.is_active = False
    bus.route = None
    bus.save(update_fields=['is_active', 'route'])
    return {
        "driver_id": driver.id,
        "bus_id": bus.id,
        "is_active": bus.is_active,
        "completed_request_id": completed.id if completed else None,
        "completed": completed is not None,
    }
