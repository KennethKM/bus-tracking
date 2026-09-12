from django.contrib import admin
from .models import (
    Route, Stop, Bus, Passenger, Ride, Notification,
    BusMovement, RideTracking, LusakaRoute, Trip
)


@admin.register(LusakaRoute)
class LusakaRouteAdmin(admin.ModelAdmin):
    list_display = ['route_number', 'name', 'origin', 'destination', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['route_number', 'name', 'origin', 'destination']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'lusaka_route', 'created_at']
    search_fields = ['name']
    list_filter = ['lusaka_route']


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'route', 'lusaka_route', 'order']
    list_filter = ['route', 'lusaka_route']
    search_fields = ['name']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'route', 'lusaka_route', 'speed', 'available_seats', 'is_active']
    list_filter = ['route', 'lusaka_route', 'is_active']
    search_fields = ['bus_number', 'driver_name']


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'phone_number']
    search_fields = ['phone_number', 'full_name']


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ['id', 'passenger', 'bus', 'status', 'pickup_location',
                    'destination_location', 'requested_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['pickup_location', 'destination_location']
    readonly_fields = ['requested_at', 'updated_at']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'passenger', 'bus', 'status', 'pickup_location',
                    'dropoff_location', 'requested_at']
    list_filter = ['status']
    search_fields = ['pickup_location', 'dropoff_location']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'passenger', 'title', 'read', 'created_at']
    list_filter = ['read', 'created_at']
    search_fields = ['title', 'message']


@admin.register(BusMovement)
class BusMovementAdmin(admin.ModelAdmin):
    list_display = ['bus', 'lat', 'lng', 'speed', 'timestamp', 'is_simulated']
    list_filter = ['is_simulated', 'timestamp']
    search_fields = ['bus__bus_number']


@admin.register(RideTracking)
class RideTrackingAdmin(admin.ModelAdmin):
    list_display = ['ride', 'current_lat', 'current_lng', 'distance_traveled',
                    'estimated_time_remaining', 'last_updated']
    search_fields = ['ride__id']