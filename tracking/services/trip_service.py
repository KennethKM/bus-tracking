from ..models import Driver


def start_trip_for_driver(driver_id):
    """Mark the assigned bus for a driver as active (start trip).

    Raises Driver.DoesNotExist if driver missing.
    Raises ValueError if driver has no assigned bus.
    Returns dict with driver_id, bus_id, is_active, and optional route info.
    """
    driver = Driver.objects.get(id=driver_id)

    if not driver.assigned_bus:
        raise ValueError("Driver has no assigned bus")

    bus = driver.assigned_bus
    bus.is_active = True
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
        "route": route,
    }
