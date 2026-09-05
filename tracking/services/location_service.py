from ..models import Bus, BusLocation, Passenger, Driver
from .stop_progression_service import advance_bus_stop_progress



def save_bus_location(bus_id, lat, lng, speed):
    # validate and coerce inputs
    try:
        lat = float(lat)
        lng = float(lng)
        speed = float(speed or 0.0)
    except (TypeError, ValueError):
        raise ValueError("lat/lng/speed must be numeric")

    # reject NaN or infinite
    from math import isfinite
    if not (isfinite(lat) and isfinite(lng) and isfinite(speed)):
        raise ValueError("lat/lng/speed must be finite numbers")

    # validate ranges
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("latitude out of range")
    if not (-180.0 <= lng <= 180.0):
        raise ValueError("longitude out of range")

    # reject 0,0 as an invalid live GPS position for this prototype
    if lat == 0.0 and lng == 0.0:
        raise ValueError("invalid GPS coordinates (0,0)")

    # sanitize speed
    if speed < 0:
        raise ValueError("speed cannot be negative")
    # cap unrealistic speed
    if speed > 200.0:
        speed = 200.0

    bus = Bus.objects.get(id=bus_id)

    bus.current_lat = lat
    bus.current_lng = lng
    bus.speed = speed

    bus.save()

    BusLocation.objects.create(
        bus=bus,
        latitude=lat,
        longitude=lng,
        speed=speed
    )

    # After successfully saving location, attempt to advance bus stop progression
    try:
        advance_bus_stop_progress(bus)
    except Exception:
        # progression must not break location API; swallow errors
        pass

    return bus


def assign_driver_to_bus(driver_id, bus_id):
    driver = Driver.objects.get(id=driver_id)
    bus = Bus.objects.get(id=bus_id)
    driver.assigned_bus = bus
    driver.save()
    return driver


def update_driver_location(driver_id, lat, lng, speed):
    driver = Driver.objects.get(id=driver_id)

    if not driver.assigned_bus:
        raise ValueError("Driver has no assigned bus")

    return save_bus_location(
        driver.assigned_bus.id,
        lat,
        lng,
        speed
    )


def save_passenger_location(
    passenger_id,
    lat,
    lng,
    active
):

    passenger = Passenger.objects.get(
        id=passenger_id
    )

    passenger.latitude = lat
    passenger.longitude = lng
    passenger.is_active = active

    passenger.save()

    return passenger