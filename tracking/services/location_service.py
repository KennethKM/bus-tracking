from ..models import Bus, BusLocation, Passenger



def save_bus_location(bus_id, lat, lng, speed):

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

    return bus



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