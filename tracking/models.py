from django.db import models

class Route(models.Model):
    name = models.CharField(max_length=100)
    origin = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Stop(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    order = models.IntegerField()

    def __str__(self):
        return self.name


class Bus(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    registration_number = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(default=40)
    current_lat = models.FloatField()
    current_lng = models.FloatField()
    current_stop_index = models.IntegerField(default=0)
    speed = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Buses"

    def __str__(self):
        return f"Bus {self.id} on {self.route.name}"


class Driver(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, blank=True)
    assigned_bus = models.ForeignKey(
        Bus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="drivers"
    )
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BusLocation(models.Model):

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)

    latitude = models.FloatField()
    longitude = models.FloatField()

    speed = models.FloatField(default=0)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bus} @ {self.timestamp}"
    
class Passenger(models.Model):

    name = models.CharField(max_length=100)

    latitude = models.FloatField()
    longitude = models.FloatField()

    is_active = models.BooleanField(default=False)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name