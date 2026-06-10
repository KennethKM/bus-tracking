from django.contrib import admin
from .models import Route, Stop, Bus, Passenger

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']

@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'route', 'order', 'latitude', 'longitude']
    list_filter = ['route']
    search_fields = ['name']

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'route', 'current_lat', 'current_lng', 'speed', 'available_seats', 'is_active']
    list_filter = ['route', 'is_active']
    search_fields = ['bus_number']

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone_number', 'current_lat', 'current_lng']
    search_fields = ['phone_number']