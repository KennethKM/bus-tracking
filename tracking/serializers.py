from rest_framework import serializers
from .models import Route, Stop, Bus, BusLocation, Passenger
from .models import Passenger

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'

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
