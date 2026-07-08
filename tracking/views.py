from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Bus, Stop, Passenger, Trip, Notification, BusMovement, TripTracking
from django.contrib.auth.models import User
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
from django.utils import timezone
import random
import math

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
        'route': s.route.name,
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
        'capacity': b.capacity,
        'driver_name': b.driver_name,
        'last_update': b.last_update.isoformat() if b.last_update else None,
    } for b in buses]
    return Response(data)

@api_view(['GET'])
def get_bus_detail(request, bus_id):
    """Get detailed bus information"""
    try:
        bus = Bus.objects.get(id=bus_id, is_active=True)
        data = {
            'id': bus.id,
            'bus_number': bus.bus_number,
            'route_name': bus.route.name,
            'current_lat': bus.current_lat,
            'current_lng': bus.current_lng,
            'speed': bus.speed,
            'available_seats': bus.available_seats,
            'occupancy': bus.occupancy_percentage,
            'capacity': bus.capacity,
            'driver_name': bus.driver_name,
            'driver_phone': bus.driver_phone,
            'last_update': bus.last_update.isoformat(),
            'route_path': bus.route.path,
        }
        return Response(data)
    except Bus.DoesNotExist:
        return Response({'error': 'Bus not found'}, status=404)

@api_view(['GET'])
def get_bus_eta_to_stop(request, bus_id, stop_id):
    """Calculate ETA from bus to specific stop"""
    try:
        bus = Bus.objects.get(id=bus_id, is_active=True)
        stop = Stop.objects.get(id=stop_id)
        
        distance = haversine_distance(bus.current_lat, bus.current_lng, stop.latitude, stop.longitude)
        eta_minutes = max(1, int((distance / max(bus.speed, 20)) * 60))
        
        return Response({
            'bus': bus.bus_number,
            'bus_id': bus.id,
            'stop': stop.name,
            'stop_id': stop.id,
            'distance_km': round(distance, 2),
            'eta_minutes': eta_minutes,
            'speed': bus.speed,
        })
    except Bus.DoesNotExist:
        return Response({'error': 'Bus not found'}, status=404)
    except Stop.DoesNotExist:
        return Response({'error': 'Stop not found'}, status=404)

@api_view(['GET'])
def get_route_path(request, route_id):
    """Get route path and stops"""
    try:
        route = Route.objects.get(id=route_id)
        stops = Stop.objects.filter(route=route)
        return Response({
            'route_id': route.id,
            'route_name': route.name,
            'path': route.path,
            'stops': [{
                'id': s.id,
                'name': s.name,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'order': s.order,
            } for s in stops]
        })
    except Route.DoesNotExist:
        return Response({'error': 'Route not found'}, status=404)

@api_view(['GET', 'POST'])
def find_nearby_buses(request):
    """Find buses near passenger location"""
    try:
        if request.method == 'POST':
            passenger_lat = request.data.get('latitude')
            passenger_lng = request.data.get('longitude')
            radius_km = request.data.get('radius_km', 10)
        else:
            passenger_lat = request.GET.get('latitude')
            passenger_lng = request.GET.get('longitude')
            radius_km = request.GET.get('radius_km', 10)
        
        if not passenger_lat or not passenger_lng:
            return Response({'error': 'Location required', 'nearby_buses': []}, status=400)
        
        passenger_lat = float(passenger_lat)
        passenger_lng = float(passenger_lng)
        radius_km = float(radius_km)
        
        buses = Bus.objects.filter(is_active=True).select_related('route')
        nearby = []
        
        for bus in buses:
            distance = haversine_distance(passenger_lat, passenger_lng, bus.current_lat, bus.current_lng)
            
            if distance <= radius_km:
                eta_minutes = max(1, int((distance / max(bus.speed, 20)) * 60))
                nearby.append({
                    'bus_id': bus.id,
                    'bus_number': bus.bus_number,
                    'route_name': bus.route.name,
                    'distance_km': round(distance, 2),
                    'eta_minutes': eta_minutes,
                    'available_seats': bus.available_seats,
                    'occupancy_percentage': bus.occupancy_percentage,
                    'speed': bus.speed,
                    'driver_name': bus.driver_name,
                })
        
        nearby.sort(key=lambda x: x['distance_km'])
        
        return Response({
            'nearby_buses': nearby,
            'count': len(nearby),
            'passenger_location': {'lat': passenger_lat, 'lng': passenger_lng}
        })
        
    except Exception as e:
        return Response({'error': str(e), 'nearby_buses': []}, status=500)

@api_view(['POST'])
def request_trip(request):
    """Passenger requests a trip"""
    try:
        passenger_id = request.data.get('passenger_id')
        pickup_lat = request.data.get('pickup_lat')
        pickup_lng = request.data.get('pickup_lng')
        dropoff_lat = request.data.get('dropoff_lat')
        dropoff_lng = request.data.get('dropoff_lng')
        pickup_location = request.data.get('pickup_location', '')
        dropoff_location = request.data.get('dropoff_location', '')
        bus_id = request.data.get('bus_id')
        
        if not passenger_id or not pickup_lat or not pickup_lng:
            return Response({'error': 'Passenger ID and pickup location required'}, status=400)
        
        passenger = get_object_or_404(Passenger, id=passenger_id)
        
        # Create trip
        trip = Trip.objects.create(
            passenger=passenger,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            pickup_location=pickup_location,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            dropoff_location=dropoff_location,
            status='requested'
        )
        
        # If bus specified, try to assign
        if bus_id:
            bus = get_object_or_404(Bus, id=bus_id, is_active=True)
            if bus.available_seats > 0:
                trip.bus = bus
                trip.status = 'assigned'
                trip.estimated_arrival = timezone.now() + timedelta(minutes=5)
                trip.save()
                
                # Create notification for passenger
                Notification.objects.create(
                    passenger=passenger,
                    title='Trip Confirmed!',
                    message=f'Bus {bus.bus_number} is on its way to you.',
                    data={'trip_id': trip.id, 'bus_id': bus.id}
                )
                
                return Response({
                    'trip_id': trip.id,
                    'status': trip.status,
                    'bus': bus.bus_number,
                    'bus_id': bus.id,
                    'estimated_arrival': trip.estimated_arrival,
                    'message': 'Trip confirmed! Bus is on its way.'
                })
        
        return Response({
            'trip_id': trip.id,
            'status': trip.status,
            'message': 'Trip requested. Waiting for bus assignment.'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_trip_status(request, trip_id):
    """Get current trip status"""
    try:
        trip = Trip.objects.get(id=trip_id)
        data = {
            'trip_id': trip.id,
            'status': trip.status,
            'bus': trip.bus.bus_number if trip.bus else None,
            'bus_id': trip.bus.id if trip.bus else None,
            'pickup_location': trip.pickup_location,
            'dropoff_location': trip.dropoff_location,
            'requested_at': trip.requested_at.isoformat(),
            'updated_at': trip.updated_at.isoformat(),
            'estimated_arrival': trip.estimated_arrival.isoformat() if trip.estimated_arrival else None,
            'bus_location': {
                'lat': trip.bus.current_lat,
                'lng': trip.bus.current_lng,
            } if trip.bus else None,
        }
        return Response(data)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=404)

@api_view(['POST'])
def rate_trip(request, trip_id):
    """Rate a completed trip"""
    try:
        trip = Trip.objects.get(id=trip_id)
        rating = request.data.get('rating')
        review = request.data.get('review', '')
        
        if not rating or not (1 <= int(rating) <= 5):
            return Response({'error': 'Rating must be between 1 and 5'}, status=400)
        
        trip.rating = rating
        trip.review = review
        trip.save()
        
        return Response({
            'message': 'Thank you for your rating!',
            'rating': rating,
        })
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=404)

@api_view(['GET'])
def get_notifications(request, passenger_id):
    """Get notifications for a passenger"""
    try:
        passenger = Passenger.objects.get(id=passenger_id)
        notifications = Notification.objects.filter(passenger=passenger).order_by('-created_at')
        
        # Mark as read
        notifications.filter(read=False).update(read=True)
        
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'read': n.read,
            'created_at': n.created_at.isoformat(),
            'data': n.data,
        } for n in notifications]
        
        return Response(data)
    except Passenger.DoesNotExist:
        return Response({'error': 'Passenger not found'}, status=404)

# ============================================
# NEW BUS MOVEMENT TRACKING FUNCTIONS
# ============================================

@api_view(['POST'])
def simulate_bus_movement(request):
    """Simulate bus movement along a route (for demo)"""
    try:
        bus_id = request.data.get('bus_id')
        trip_id = request.data.get('trip_id')
        
        if not bus_id:
            return Response({'error': 'Bus ID required'}, status=400)
        
        bus = Bus.objects.get(id=bus_id)
        
        # Start movement simulation
        # Calculate a random destination near the bus
        dest_lat = bus.current_lat + random.uniform(-0.01, 0.01)
        dest_lng = bus.current_lng + random.uniform(-0.01, 0.01)
        
        # Simulate movement steps
        steps = 20
        lat_step = (dest_lat - bus.current_lat) / steps
        lng_step = (dest_lng - bus.current_lng) / steps
        
        movement_data = []
        current_lat = bus.current_lat
        current_lng = bus.current_lng
        
        for i in range(steps):
            current_lat += lat_step
            current_lng += lng_step
            speed = random.randint(15, 45)  # Random speed 15-45 km/h
            
            # Update bus location
            bus.current_lat = current_lat
            bus.current_lng = current_lng
            bus.speed = speed
            bus.save()
            
            # Record movement
            BusMovement.objects.create(
                bus=bus,
                lat=current_lat,
                lng=current_lng,
                speed=speed,
                is_simulated=True
            )
            
            movement_data.append({
                'lat': current_lat,
                'lng': current_lng,
                'speed': speed
            })
        
        return Response({
            'success': True,
            'message': f'Bus {bus.bus_number} is moving',
            'movement': movement_data
        })
        
    except Bus.DoesNotExist:
        return Response({'error': 'Bus not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_bus_movement(request, bus_id):
    """Get bus movement history"""
    try:
        bus = Bus.objects.get(id=bus_id)
        movements = BusMovement.objects.filter(bus=bus)[:50]  # Last 50 movements
        
        data = [{
            'lat': m.lat,
            'lng': m.lng,
            'speed': m.speed,
            'heading': m.heading,
            'timestamp': m.timestamp.isoformat(),
            'is_simulated': m.is_simulated
        } for m in movements]
        
        return Response({
            'bus_id': bus.id,
            'bus_number': bus.bus_number,
            'current_location': {
                'lat': bus.current_lat,
                'lng': bus.current_lng,
                'speed': bus.speed
            },
            'movement_history': data
        })
    except Bus.DoesNotExist:
        return Response({'error': 'Bus not found'}, status=404)

@api_view(['POST'])
def start_trip_tracking(request):
    """Start tracking a passenger's trip"""
    try:
        trip_id = request.data.get('trip_id')
        bus_id = request.data.get('bus_id')
        
        trip = Trip.objects.get(id=trip_id)
        bus = Bus.objects.get(id=bus_id)
        
        # Create tracking record
        tracking, created = TripTracking.objects.get_or_create(
            trip=trip,
            defaults={
                'current_lat': bus.current_lat,
                'current_lng': bus.current_lng,
                'estimated_time_remaining': 15
            }
        )
        
        # Update trip status
        trip.status = 'in_progress'
        trip.bus = bus
        trip.save()
        
        # Start movement simulation for this bus
        # (In production, this would be real GPS data)
        
        return Response({
            'success': True,
            'trip_id': trip.id,
            'tracking_id': tracking.id,
            'bus_location': {
                'lat': bus.current_lat,
                'lng': bus.current_lng
            },
            'estimated_time_remaining': tracking.estimated_time_remaining
        })
        
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=404)
    except Bus.DoesNotExist:
        return Response({'error': 'Bus not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_trip_tracking(request, trip_id):
    """Get real-time trip tracking information"""
    try:
        trip = Trip.objects.get(id=trip_id)
        tracking = TripTracking.objects.get(trip=trip)
        bus = trip.bus
        
        if not bus:
            return Response({'error': 'No bus assigned to this trip'}, status=404)
        
        # Calculate distance to destination (if dropoff exists)
        distance_to_dest = 0
        if trip.dropoff_lat and trip.dropoff_lng:
            distance_to_dest = haversine_distance(
                bus.current_lat, bus.current_lng,
                trip.dropoff_lat, trip.dropoff_lng
            )
        
        eta_minutes = max(1, int((distance_to_dest / max(bus.speed, 20)) * 60))
        
        return Response({
            'trip_id': trip.id,
            'status': trip.status,
            'bus': {
                'id': bus.id,
                'number': bus.bus_number,
                'current_lat': bus.current_lat,
                'current_lng': bus.current_lng,
                'speed': bus.speed
            },
            'passenger_location': {
                'lat': tracking.current_lat,
                'lng': tracking.current_lng
            },
            'distance_to_destination': round(distance_to_dest, 2),
            'eta_minutes': eta_minutes,
            'distance_traveled': tracking.distance_traveled,
            'last_updated': tracking.last_updated.isoformat()
        })
        
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=404)
    except TripTracking.DoesNotExist:
        return Response({'error': 'Tracking not found'}, status=404)

def index(request):
    """Main page view"""
    return render(request, 'tracking/index.html')
