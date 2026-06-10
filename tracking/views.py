from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Bus, Stop, Passenger
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lng1, lat2, lng2 = map(float, [lat1, lng1, lat2, lng2])
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

@api_view(['GET'])
def get_all_stops(request):
    """Get all bus stops"""
    stops = Stop.objects.all().select_related('route')
    data = [{
        'id': s.id,
        'name': s.name,
        'latitude': s.latitude,
        'longitude': s.longitude,
    } for s in stops]
    return Response(data)

@api_view(['GET'])
def get_all_buses(request):
    """Get all active buses"""
    buses = Bus.objects.filter(is_active=True).select_related('route')
    data = [{
        'id': b.id,
        'bus_number': b.bus_number,
        'route_name': b.route.name,
        'current_lat': b.current_lat,
        'current_lng': b.current_lng,
        'speed': b.speed,
        'available_seats': b.available_seats,
        'occupancy': b.occupancy_percentage,
        'capacity': b.capacity
    } for b in buses]
    return Response(data)

@api_view(['GET'])
def find_nearby_buses(request):
    """Find buses near passenger location"""
    try:
        # Get parameters from URL
        passenger_lat = request.GET.get('latitude')
        passenger_lng = request.GET.get('longitude')
        radius_km = request.GET.get('radius_km', 10)
        
        print(f"📍 Finding nearby buses - Lat: {passenger_lat}, Lng: {passenger_lng}, Radius: {radius_km}km")
        
        # Validate input
        if not passenger_lat or not passenger_lng:
            return Response({
                'error': 'Latitude and longitude required',
                'nearby_buses': []
            }, status=400)
        
        # Convert to float
        passenger_lat = float(passenger_lat)
        passenger_lng = float(passenger_lng)
        radius_km = float(radius_km)
        
        # Get all active buses
        buses = Bus.objects.filter(is_active=True).select_related('route')
        print(f"📡 Total active buses: {buses.count()}")
        
        nearby = []
        
        for bus in buses:
            # Calculate distance
            distance = haversine_distance(passenger_lat, passenger_lng, bus.current_lat, bus.current_lng)
            
            print(f"  Bus {bus.bus_number}: distance = {distance:.2f}km")
            
            # Check if within radius
            if distance <= radius_km:
                # Calculate ETA in minutes
                if bus.speed > 0:
                    eta_minutes = int((distance / bus.speed) * 60)
                else:
                    eta_minutes = int((distance / 20) * 60)  # Assume 20 km/h if speed is 0
                
                eta_minutes = max(1, eta_minutes)  # Minimum 1 minute
                
                nearby.append({
                    'bus_id': bus.id,
                    'bus_number': bus.bus_number,
                    'route_name': bus.route.name,
                    'distance_km': round(distance, 2),
                    'eta_minutes': eta_minutes,
                    'available_seats': bus.available_seats,
                    'occupancy_percentage': bus.occupancy_percentage,
                    'speed': bus.speed
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance_km'])
        
        print(f"✅ Found {len(nearby)} buses within {radius_km}km")
        
        return Response({
            'nearby_buses': nearby,
            'count': len(nearby),
            'passenger_location': {'lat': passenger_lat, 'lng': passenger_lng}
        })
        
    except Exception as e:
        print(f"❌ Error in find_nearby_buses: {str(e)}")
        return Response({
            'error': str(e),
            'nearby_buses': []
        }, status=500)

def index(request):
    """Main page view"""
    return render(request, 'tracking/index.html')