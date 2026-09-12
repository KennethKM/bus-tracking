from django.db import models
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


class LusakaRoute(models.Model):
    """Real Lusaka bus routes from OpenStreetMap"""
    route_number = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    waypoints = models.JSONField(default=list)
    stops_list = models.JSONField(default=list)  # List of stop names
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Route {self.route_number}: {self.name}"


class Route(models.Model):
    """Internal route model for bus movement"""
    name = models.CharField(max_length=100)
    path = models.JSONField(default=list)
    waypoints = models.JSONField(default=list, blank=True)
    distance_km = models.FloatField(default=0)
    estimated_time = models.IntegerField(default=30)
    lusaka_route = models.ForeignKey(
        LusakaRoute, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='internal_routes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    lusaka_route = models.ForeignKey(
        LusakaRoute, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='buses'
    )
    current_lat = models.FloatField(default=0)
    current_lng = models.FloatField(default=0)
    speed = models.FloatField(default=0)
    capacity = models.IntegerField(default=65)
    occupied_seats = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    driver_phone = models.CharField(max_length=20, blank=True, null=True)
    route_progress = models.FloatField(default=0)
    direction = models.CharField(max_length=10, default='forward')
    scheduled_stops = models.JSONField(default=list, blank=True)

    @property
    def available_seats(self):
        return self.capacity - self.occupied_seats

    @property
    def occupancy_percentage(self):
        return (self.occupied_seats / self.capacity) * 100 if self.capacity > 0 else 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'bus_updates',
                {
                    'type': 'bus_update',
                    'bus_id': self.id,
                    'bus_number': self.bus_number,
                    'lat': self.current_lat,
                    'lng': self.current_lng,
                    'speed': self.speed,
                    'available_seats': self.available_seats,
                    'occupancy': self.occupancy_percentage,
                    'route_progress': self.route_progress,
                    'direction': self.direction
                }
            )
        except:
            pass

    def __str__(self):
        return f"{self.bus_number} - {self.route.name}"


class Stop(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    lusaka_route = models.ForeignKey(
        LusakaRoute, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='route_stops'
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Passenger(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    notification_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.full_name or f"Passenger {self.user.username if self.user else self.id}"


class Ride(models.Model):
    """Ride request feature"""
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('searching', 'Searching for Bus'),
        ('assigned', 'Bus Assigned'),
        ('arriving', 'Bus Arriving'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='rides')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='rides')

    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    pickup_location = models.CharField(max_length=200, blank=True)
    pickup_stop_name = models.CharField(max_length=200, blank=True)

    destination_lat = models.FloatField(null=True, blank=True)
    destination_lng = models.FloatField(null=True, blank=True)
    destination_location = models.CharField(max_length=200, blank=True)
    destination_stop_name = models.CharField(max_length=200, blank=True)

    lusaka_route = models.ForeignKey(
        LusakaRoute, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rides'
    )
    requested_route_name = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    review = models.TextField(blank=True)

    def __str__(self):
        return f"Ride {self.id} - {self.status}"


class Trip(models.Model):
    """Legacy Trip model for backward compatibility"""
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='trips')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='trips')
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    dropoff_lat = models.FloatField(null=True, blank=True)
    dropoff_lng = models.FloatField(null=True, blank=True)
    pickup_location = models.CharField(max_length=200, blank=True)
    dropoff_location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    review = models.TextField(blank=True)

    def __str__(self):
        return f"Trip {self.id} - {self.status}"


class Notification(models.Model):
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Notification for {self.passenger} - {self.title}"


class BusMovement(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='movements')
    lat = models.FloatField()
    lng = models.FloatField()
    speed = models.FloatField(default=0)
    heading = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_simulated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.bus.bus_number} - {self.timestamp}"


class RideTracking(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='tracking')
    current_lat = models.FloatField()
    current_lng = models.FloatField()
    distance_traveled = models.FloatField(default=0)
    estimated_time_remaining = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tracking Ride {self.ride.id}"


class TripTracking(models.Model):
    """Legacy TripTracking for backward compatibility"""
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='tracking')
    current_lat = models.FloatField()
    current_lng = models.FloatField()
    distance_traveled = models.FloatField(default=0)
    estimated_time_remaining = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tracking Trip {self.trip.id}"