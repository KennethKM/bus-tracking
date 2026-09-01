from ..models import Bus, Passenger
from .status_service import get_bus_status
from .next_stop_service import update_next_stop


def save_bus_location(
    registration_number,
    lat,
    lng,
    speed
):

    bus = Bus.objects.get(
        registration_number=registration_number
    )

    bus.current_lat = lat
    bus.current_lng = lng
    bus.speed = speed
    
    update_next_stop(bus)
    
    bus.status = get_bus_status(bus)

    bus.save()

    

    return bus
    
   



