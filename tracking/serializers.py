from rest_framework import serializers
from .models import Bus, Stop, Route, Trip, Passenger

class BusSerializer(serializers.ModelSerializer):
    available_seats = serializers.IntegerField(read_only=True)
    occupancy_percentage = serializers.FloatField(read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    
    class Meta:
        model = Bus
        fields = ['id', 'bus_number', 'route_name', 'current_lat', 'current_lng', 
                 'speed', 'available_seats', 'occupancy_percentage', 'is_active',
                 'driver_name', 'last_update']

class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'name', 'latitude', 'longitude', 'order']

class RouteSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)
    
    class Meta:
        model = Route
        fields = ['id', 'name', 'path', 'stops']

class TripSerializer(serializers.ModelSerializer):
    bus_number = serializers.CharField(source='bus.bus_number', read_only=True)
    passenger_name = serializers.CharField(source='passenger.full_name', read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'passenger', 'bus', 'bus_number', 'passenger_name',
                 'pickup_location', 'dropoff_location', 'status', 
                 'requested_at', 'estimated_arrival', 'fare', 'rating', 'review']