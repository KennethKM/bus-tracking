# tracking/utils.py (create new file)
from math import radians, sin, cos, sqrt, atan2
from .models import Bus, Stop
import datetime

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate the great circle distance between two points in km"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def calculate_eta(bus, stop):
    """Calculate ETA in minutes based on distance and bus speed"""
    distance = haversine_distance(bus.current_lat, bus.current_lng, stop.latitude, stop.longitude)
    
    if bus.speed > 0:
        eta_hours = distance / bus.speed
        eta_minutes = eta_hours * 60
    else:
        # Default to 30 km/h if speed is 0
        eta_minutes = (distance / 30) * 60
    
    return max(1, int(eta_minutes))  # Minimum 1 minute

def find_nearby_buses(passenger_lat, passenger_lng, radius_km=5):
    """Find buses within specified radius"""
    nearby = []
    buses = Bus.objects.filter(is_active=True)
    
    for bus in buses:
        distance = haversine_distance(passenger_lat, passenger_lng, bus.current_lat, bus.current_lng)
        if distance <= radius_km:
            nearby.append({
                'bus_id': bus.id,
                'bus_number': bus.bus_number,
                'route_name': bus.route.name,
                'distance_km': round(distance, 2),
                'eta_minutes': calculate_eta(bus, None)  # Simplified ETA
            })
    
    return sorted(nearby, key=lambda x: x['distance_km'])