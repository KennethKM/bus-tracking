from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import (Bus, Stop, Passenger, Ride, Notification, BusMovement,
                     RideTracking, Route, LusakaRoute, Trip)
from django.contrib.auth.models import User
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
from django.utils import timezone
import json
import random
import math


def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371
    lat1, lng1, lat2, lng2 = map(float, [lat1, lng1, lat2, lng2])
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# ============================================
# LUSAKA ROUTES
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def get_lusaka_routes(request):
    """Get all Lusaka bus routes with stops"""
    try:
        routes = LusakaRoute.objects.filter(is_active=True)
        data = [{
            'id': r.id,
            'route_number': r.route_number,
            'name': r.name,
            'origin': r.origin,
            'destination': r.destination,
            'waypoints': r.waypoints,
            'stops': r.stops_list,
        } for r in routes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_buses_on_route(request, route_id):
    """Get available buses on a specific Lusaka route"""
    try:
        lusaka_route = LusakaRoute.objects.get(id=route_id)
        buses = Bus.objects.filter(lusaka_route=lusaka_route, is_active=True)

        data = [{
            'id': b.id,
            'bus_number': b.bus_number,
            'route_name': lusaka_route.name,
            'route_number': lusaka_route.route_number,
            'current_lat': b.current_lat,
            'current_lng': b.current_lng,
            'speed': b.speed,
            'available_seats': b.available_seats,
            'occupancy': b.occupancy_percentage,
            'capacity': b.capacity,
            'driver_name': b.driver_name,
            'route_progress': b.route_progress,
            'direction': b.direction,
            'last_update': b.last_update.isoformat() if b.last_update else None,
        } for b in buses]

        return JsonResponse({
            'route_id': lusaka_route.id,
            'route_number': lusaka_route.route_number,
            'route_name': lusaka_route.name,
            'origin': lusaka_route.origin,
            'destination': lusaka_route.destination,
            'stops': lusaka_route.stops_list,
            'buses': data,
            'bus_count': len(data)
        })
    except LusakaRoute.DoesNotExist:
        return JsonResponse({'error': 'Route not found'}, status=404)


# ============================================
# BUSES AND STOPS
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def get_all_buses(request):
    try:
        buses = Bus.objects.filter(is_active=True).select_related('route', 'lusaka_route')
        data = [{
            'id': b.id,
            'bus_number': b.bus_number,
            'route_name': b.route.name,
            'route_number': b.lusaka_route.route_number if b.lusaka_route else '',
            'current_lat': b.current_lat,
            'current_lng': b.current_lng,
            'speed': b.speed,
            'available_seats': b.available_seats,
            'occupancy': b.occupancy_percentage,
            'capacity': b.capacity,
            'driver_name': b.driver_name,
            'route_progress': b.route_progress,
            'direction': b.direction,
            'last_update': b.last_update.isoformat() if b.last_update else None,
        } for b in buses]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_stops(request):
    try:
        stops = Stop.objects.all().select_related('route')
        data = [{
            'id': s.id,
            'name': s.name,
            'latitude': s.latitude,
            'longitude': s.longitude,
            'route': s.route.name,
            'order': s.order,
        } for s in stops]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_bus_detail(request, bus_id):
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
            'route_progress': bus.route_progress,
            'direction': bus.direction,
            'last_update': bus.last_update.isoformat(),
            'waypoints': bus.route.waypoints,
        }
        return JsonResponse(data)
    except Bus.DoesNotExist:
        return JsonResponse({'error': 'Bus not found'}, status=404)


@csrf_exempt
@require_http_methods(["GET"])
def get_route_path(request, route_id):
    try:
        route = Route.objects.get(id=route_id)
        stops = Stop.objects.filter(route=route)
        return JsonResponse({
            'route_id': route.id,
            'route_name': route.name,
            'path': route.path,
            'waypoints': route.waypoints,
            'stops': [{'id': s.id, 'name': s.name, 'latitude': s.latitude,
                       'longitude': s.longitude, 'order': s.order} for s in stops]
        })
    except Route.DoesNotExist:
        return JsonResponse({'error': 'Route not found'}, status=404)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def find_nearby_buses(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            passenger_lat = data.get('latitude')
            passenger_lng = data.get('longitude')
            radius_km = data.get('radius_km', 10)
        else:
            passenger_lat = request.GET.get('latitude')
            passenger_lng = request.GET.get('longitude')
            radius_km = request.GET.get('radius_km', 10)

        if not passenger_lat or not passenger_lng:
            return JsonResponse({'error': 'Location required', 'nearby_buses': []}, status=400)

        passenger_lat = float(passenger_lat)
        passenger_lng = float(passenger_lng)
        radius_km = float(radius_km)

        buses = Bus.objects.filter(is_active=True).select_related('route', 'lusaka_route')
        nearby = []

        for bus in buses:
            distance = haversine_distance(passenger_lat, passenger_lng, bus.current_lat, bus.current_lng)
            if distance <= radius_km:
                eta_minutes = max(1, int((distance / max(bus.speed, 20)) * 60))
                nearby.append({
                    'bus_id': bus.id,
                    'bus_number': bus.bus_number,
                    'route_name': bus.route.name,
                    'route_number': bus.lusaka_route.route_number if bus.lusaka_route else '',
                    'distance_km': round(distance, 2),
                    'eta_minutes': eta_minutes,
                    'available_seats': bus.available_seats,
                    'occupancy_percentage': bus.occupancy_percentage,
                    'speed': bus.speed,
                    'driver_name': bus.driver_name,
                })

        nearby.sort(key=lambda x: x['distance_km'])

        return JsonResponse({
            'nearby_buses': nearby,
            'count': len(nearby),
            'passenger_location': {'lat': passenger_lat, 'lng': passenger_lng}
        })
    except Exception as e:
        return JsonResponse({'error': str(e), 'nearby_buses': []}, status=500)


# ============================================
# RIDE REQUEST FEATURE
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def request_ride(request):
    """Request a ride with destination and route selection"""
    try:
        data = json.loads(request.body)
        passenger_id = data.get('passenger_id')

        pickup_lat = data.get('pickup_lat')
        pickup_lng = data.get('pickup_lng')
        pickup_location = data.get('pickup_location', '')
        pickup_stop_name = data.get('pickup_stop_name', '')

        destination_lat = data.get('destination_lat')
        destination_lng = data.get('destination_lng')
        destination_location = data.get('destination_location', '')
        destination_stop_name = data.get('destination_stop_name', '')

        lusaka_route_id = data.get('lusaka_route_id')
        bus_id = data.get('bus_id')

        print(f"🚗 Ride Request - Passenger: {passenger_id}")
        print(f"📍 Pickup: {pickup_lat}, {pickup_lng}")
        print(f"🎯 Destination: {destination_location}")
        print(f"🛣️ Route: {lusaka_route_id}")

        if not passenger_id:
            passenger, created = Passenger.objects.get_or_create(
                id=1,
                defaults={'phone_number': '+260900000000', 'full_name': 'Default Passenger'}
            )
            passenger_id = passenger.id

        passenger = get_object_or_404(Passenger, id=passenger_id)

        lusaka_route = None
        if lusaka_route_id:
            try:
                lusaka_route = LusakaRoute.objects.get(id=lusaka_route_id)
            except LusakaRoute.DoesNotExist:
                pass

        ride = Ride.objects.create(
            passenger=passenger,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            pickup_location=pickup_location or f"Location at {pickup_lat}, {pickup_lng}",
            pickup_stop_name=pickup_stop_name,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            destination_location=destination_location,
            destination_stop_name=destination_stop_name,
            lusaka_route=lusaka_route,
            requested_route_name=lusaka_route.name if lusaka_route else '',
            status='searching'
        )

        print(f"✅ Ride created: {ride.id}")

        assigned_bus = None
        if bus_id:
            try:
                assigned_bus = Bus.objects.get(id=bus_id, is_active=True)
            except Bus.DoesNotExist:
                pass

        if not assigned_bus and lusaka_route:
            available_buses = Bus.objects.filter(
                lusaka_route=lusaka_route, is_active=True
            ).order_by('route_progress')
            if available_buses.exists():
                assigned_bus = available_buses.first()

        if assigned_bus:
            ride.bus = assigned_bus
            ride.status = 'assigned'
            ride.estimated_arrival = timezone.now() + timedelta(minutes=5)
            ride.save()

            Notification.objects.create(
                passenger=passenger,
                title='Ride Confirmed!',
                message=f'Bus {assigned_bus.bus_number} is on its way to you.',
                data={'ride_id': ride.id, 'bus_id': assigned_bus.id}
            )

            return JsonResponse({
                'ride_id': ride.id,
                'status': ride.status,
                'bus': assigned_bus.bus_number,
                'bus_id': assigned_bus.id,
                'route_number': lusaka_route.route_number if lusaka_route else '',
                'route_name': lusaka_route.name if lusaka_route else '',
                'destination': destination_location or destination_stop_name,
                'estimated_arrival': ride.estimated_arrival.isoformat() if ride.estimated_arrival else None,
                'message': f'Bus {assigned_bus.bus_number} is on its way!'
            })

        return JsonResponse({
            'ride_id': ride.id,
            'status': ride.status,
            'message': 'Ride requested. Searching for available bus...'
        })

    except Exception as e:
        print(f"❌ Error in request_ride: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_ride_tracking(request, ride_id):
    """Get real-time ride tracking"""
    try:
        ride = Ride.objects.get(id=ride_id)
        bus = ride.bus

        if not bus:
            return JsonResponse({'error': 'No bus assigned to this ride'}, status=404)

        try:
            tracking = RideTracking.objects.get(ride=ride)
        except RideTracking.DoesNotExist:
            tracking = RideTracking.objects.create(
                ride=ride,
                current_lat=bus.current_lat,
                current_lng=bus.current_lng,
                estimated_time_remaining=15
            )

        distance_to_dest = 0
        if ride.destination_lat and ride.destination_lng:
            distance_to_dest = haversine_distance(
                bus.current_lat, bus.current_lng,
                ride.destination_lat, ride.destination_lng
            )

        eta_minutes = max(1, int((distance_to_dest / max(bus.speed, 20)) * 60))

        return JsonResponse({
            'ride_id': ride.id,
            'status': ride.status,
            'bus': {
                'id': bus.id,
                'number': bus.bus_number,
                'current_lat': bus.current_lat,
                'current_lng': bus.current_lng,
                'speed': bus.speed,
                'route_progress': bus.route_progress,
                'direction': bus.direction,
            },
            'pickup_location': ride.pickup_location,
            'destination_location': ride.destination_location,
            'requested_route_name': ride.requested_route_name,
            'distance_to_destination': round(distance_to_dest, 2),
            'eta_minutes': eta_minutes,
            'last_updated': tracking.last_updated.isoformat()
        })
    except Ride.DoesNotExist:
        return JsonResponse({'error': 'Ride not found'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def start_ride_tracking(request):
    try:
        data = json.loads(request.body)
        ride_id = data.get('ride_id')
        bus_id = data.get('bus_id')

        ride = Ride.objects.get(id=ride_id)
        bus = Bus.objects.get(id=bus_id)

        tracking, created = RideTracking.objects.get_or_create(
            ride=ride,
            defaults={
                'current_lat': bus.current_lat,
                'current_lng': bus.current_lng,
                'estimated_time_remaining': 15
            }
        )

        ride.status = 'in_progress'
        ride.bus = bus
        ride.save()

        return JsonResponse({
            'success': True,
            'ride_id': ride.id,
            'tracking_id': tracking.id,
            'bus_location': {
                'lat': bus.current_lat,
                'lng': bus.current_lng,
                'speed': bus.speed,
            },
            'estimated_time_remaining': tracking.estimated_time_remaining
        })
    except Ride.DoesNotExist:
        return JsonResponse({'error': 'Ride not found'}, status=404)
    except Bus.DoesNotExist:
        return JsonResponse({'error': 'Bus not found'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def rate_ride(request, ride_id):
    try:
        data = json.loads(request.body)
        ride = Ride.objects.get(id=ride_id)
        rating = data.get('rating')
        review = data.get('review', '')

        if not rating or not (1 <= int(rating) <= 5):
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)

        ride.rating = rating
        ride.review = review
        ride.save()

        return JsonResponse({'message': 'Thank you for your rating!', 'rating': rating})
    except Ride.DoesNotExist:
        return JsonResponse({'error': 'Ride not found'}, status=404)


@csrf_exempt
@require_http_methods(["GET"])
def get_notifications(request, passenger_id):
    try:
        passenger = Passenger.objects.get(id=passenger_id)
        notifications = Notification.objects.filter(passenger=passenger).order_by('-created_at')
        notifications.filter(read=False).update(read=True)

        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'read': n.read,
            'created_at': n.created_at.isoformat(),
            'data': n.data,
        } for n in notifications]

        return JsonResponse(data, safe=False)
    except Passenger.DoesNotExist:
        return JsonResponse({'error': 'Passenger not found'}, status=404)


# ============================================
# BUS MOVEMENT SIMULATION
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def start_route_simulation(request):
    """Simulate movement for all active buses"""
    try:
        buses = Bus.objects.filter(is_active=True)
        results = []

        for bus in buses:
            try:
                if bus.route_progress is None:
                    bus.route_progress = random.uniform(0, 1)
                    bus.direction = random.choice(['forward', 'reverse'])

                if bus.direction == 'forward':
                    bus.route_progress += random.uniform(0.005, 0.02)
                else:
                    bus.route_progress -= random.uniform(0.005, 0.02)

                if bus.route_progress >= 1:
                    bus.route_progress = 1
                    bus.direction = 'reverse'
                    speed = 0
                elif bus.route_progress <= 0:
                    bus.route_progress = 0
                    bus.direction = 'forward'
                    speed = 0
                else:
                    speed = random.randint(15, 45)

                waypoints = bus.route.waypoints
                if not waypoints:
                    continue

                total_waypoints = len(waypoints)
                index = bus.route_progress * (total_waypoints - 1)
                idx1 = int(index)
                idx2 = min(idx1 + 1, total_waypoints - 1)
                fraction = index - idx1

                if idx1 < total_waypoints and idx2 < total_waypoints:
                    lat = waypoints[idx1][0] + (waypoints[idx2][0] - waypoints[idx1][0]) * fraction
                    lng = waypoints[idx1][1] + (waypoints[idx2][1] - waypoints[idx1][1]) * fraction
                else:
                    lat = waypoints[-1][0]
                    lng = waypoints[-1][1]

                bus.current_lat = lat
                bus.current_lng = lng
                bus.speed = speed
                bus.last_update = timezone.now()
                bus.save()

                BusMovement.objects.create(
                    bus=bus, lat=lat, lng=lng, speed=speed,
                    heading=random.randint(0, 360), is_simulated=True
                )

                results.append({
                    'bus_id': bus.id,
                    'bus_number': bus.bus_number,
                    'status': 'success',
                    'route_progress': bus.route_progress
                })
            except Exception as e:
                results.append({
                    'bus_id': bus.id,
                    'bus_number': bus.bus_number,
                    'status': 'error',
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'message': f'Simulated {len(results)} buses',
            'results': results
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def index(request):
    """Main page view"""
    return render(request, 'tracking/index.html')