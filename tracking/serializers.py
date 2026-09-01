from rest_framework import serializers
from .models import (
    Route,
    Stop,
    Bus,
    Passenger,
    WaitingRequest,
    Trip
)



class DriverSessionSerializer(serializers.ModelSerializer):
    has_resumable_trip = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    last_stop = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            "has_resumable_trip",
            "route",
            "destination",
            "last_stop",
            "last_updated",
            "status",
        ]

    def get_has_resumable_trip(self, obj):
        return obj.current_trip is not None

    def get_route(self, obj):
        if obj.current_trip:
            return obj.current_trip.route.route_long_name
        return None

    def get_destination(self, obj):
        if obj.current_trip:
            return obj.current_trip.trip_headsign
        return None

    def get_last_stop(self, obj):
        if obj.current_stop_time:
            return obj.current_stop_time.stop.stop_name
        return None




class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'

class RouteSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = [
            "route_id",
            "route_long_name",
        ]



class RouteDestinationSerializer(serializers.Serializer):

    destination = serializers.CharField()


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = '__all__'


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = '__all__'


class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = '__all__'


class WaitingRequestSerializer(serializers.ModelSerializer):

    passenger_name = serializers.CharField(
        source="passenger.name",
        read_only=True
    )

    route_name = serializers.CharField(
    source="route.name",
    read_only=True
    )

    stop_name = serializers.CharField(
        source="stop.name",
        read_only=True
    )

    class Meta:
        model = WaitingRequest
        fields = [
            "id",
            "status",
            "created_at",
            "deactivated_at",
            "passenger",
            "route",
            "stop",
            "passenger_name",
            "route_name",
            "stop_name",
        ]





class StartTripSerializer(serializers.Serializer):

    registration_number = serializers.CharField(
        max_length=20
    )

    route_id = serializers.CharField(
        max_length=100
    )

    destination = serializers.CharField(
        max_length=255
    )


