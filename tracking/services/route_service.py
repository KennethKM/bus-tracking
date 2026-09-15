from ..models import Bus, Passenger
from .eta_service import calculate_eta


def get_active_buses():
    return Bus.objects.filter(is_active=True)





