from django.db import models, transaction
from django.core.exceptions import ValidationError



class Route(models.Model):
    route_id = models.CharField(
        max_length=50,
        primary_key=True
    )

    route_long_name = models.CharField(
        max_length=255
    )

    continuous_pickup = models.IntegerField(
        default=0
    )

    continuous_drop_off = models.IntegerField(
        default=0
    )

    def __str__(self):
        return self.route_long_name


class Stop(models.Model):

    stop_id = models.IntegerField(
        primary_key=True
    )

    stop_name = models.CharField(
        max_length=255
    )

    stop_lat = models.FloatField()

    stop_lon = models.FloatField()

    def __str__(self):
        return self.stop_name


class Trip(models.Model):

    trip_id = models.CharField(
        max_length=100,
        primary_key=True
    )

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE
    )

    trip_headsign = models.CharField(
        max_length=255
    )

    direction_id = models.IntegerField()

    shape_id = models.CharField(
        max_length=100
    )

    service_id = models.CharField(
        max_length=100
    )

    def __str__(self):
        return f"{self.route.route_long_name} -> {self.trip_headsign}"


class StopTime(models.Model):

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE
    )

    stop = models.ForeignKey(
        Stop,
        on_delete=models.CASCADE
    )

    stop_sequence = models.IntegerField()

    class Meta:
        ordering = ["stop_sequence"]

        constraints = [
            models.UniqueConstraint(
                fields=["trip", "stop_sequence"],
                name="unique_stop_sequence_per_trip"
            )
        ]

    def __str__(self):
        return (
            f"{self.trip.trip_headsign} - "
            f"{self.stop.stop_name} "
            f"({self.stop_sequence})"
        )





class Bus(models.Model):

    STATUS_CHOICES = [
        ("IDLE", "Idle"),
        ("IN_TRANSIT", "In Transit"),
        ("AT_STOP", "At Stop"),
    ]

    registration_number = models.CharField(
        max_length=20,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IDLE"
    )

    current_trip = models.ForeignKey(
        'Trip',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    current_stop_time = models.ForeignKey(
        'StopTime',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    current_lat = models.FloatField(
        null=True,
        blank=True
    )

    current_lng = models.FloatField(
        null=True,
        blank=True
    )

    speed = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Buses"

    def __str__(self):
        return self.registration_number

    def reset_operational_state(self):
        self.status = "IDLE"
        self.current_trip = None
        self.current_stop_time = None
        self.current_lat = None
        self.current_lng = None
        self.speed = 0

    def activate(self):
        with transaction.atomic():
            self.is_active = True
            self.save()

    def deactivate(self):
        with transaction.atomic():
            self.is_active = False
            self.reset_operational_state()
            self.save()

    def start_fresh(self):
        with transaction.atomic():
            self.reset_operational_state()
            self.save()
    


class Passenger(models.Model):

    name = models.CharField(max_length=100)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    


class WaitingRequest(models.Model):

    STATUS_CHOICES = [
        ("WAITING", "Waiting"),
        ("ON_BOARD", "On Board"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
        ("COMPLETED", "Completed"),
    ]

    passenger = models.ForeignKey(
    Passenger,
    on_delete=models.CASCADE,
    related_name="waiting_requests"
    )

    route = models.ForeignKey(
    Route,
    on_delete=models.CASCADE,
    related_name="waiting_requests"
    )

    stop = models.ForeignKey(
    Stop,
    on_delete=models.CASCADE,
    related_name="waiting_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="WAITING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    deactivated_at = models.DateTimeField(
        null=True,
        blank=True
    )


    def clean(self):

        if self.status not in ["WAITING", "ON_BOARD"]:
            return

        active_request_exists = WaitingRequest.objects.filter(
            passenger=self.passenger,
            status__in=["WAITING", "ON_BOARD"]
        ).exclude(
            id=self.id
        ).exists()

        if active_request_exists:
            raise ValidationError(
                "Passenger already has an active trip."
            )
    
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.passenger.name} "
            f"waiting at {self.stop.stop_name}"
    )



class Shape(models.Model):

    shape_id = models.CharField(max_length=100)

    shape_pt_lat = models.FloatField()

    shape_pt_lon = models.FloatField()

    shape_pt_sequence = models.IntegerField()

    class Meta:
        ordering = ["shape_pt_sequence"]

        constraints = [
            models.UniqueConstraint(
                fields=["shape_id", "shape_pt_sequence"],
                name="unique_shape_point"
            )
        ]