# tracking/models.py
from django.db import models
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class Route(models.Model):
    name = models.CharField(max_length=100)
    path = models.JSONField()  # List of [lat, lng] coordinates
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    current_lat = models.FloatField(default=0)
    current_lng = models.FloatField(default=0)
    speed = models.FloatField(default=0)  # km/h
    capacity = models.IntegerField(default=65)
    occupied_seats = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    @property
    def available_seats(self):
        return self.capacity - self.occupied_seats

    @property
    def occupancy_percentage(self):
        return (self.occupied_seats / self.capacity) * 100 if self.capacity > 0 else 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Send WebSocket update when bus location changes
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
                'occupancy': self.occupancy_percentage
            }
        )

    def __str__(self):
        return f"{self.bus_number} - {self.route.name}"

class Stop(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
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

    def __str__(self):
        return f"Passenger {self.user.username if self.user else self.id}"

class Trip(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('assigned', 'Assigned'),
        ('en_route', 'En Route'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='trips')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='trips')
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Trip {self.id} - {self.status}"