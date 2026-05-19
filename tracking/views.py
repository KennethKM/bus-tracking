from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Route, Stop, Bus, BusLocation, Passenger

from .serializers import (
    RouteSerializer,
    StopSerializer,
    BusSerializer,
    PassengerSerializer
)

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class StopViewSet(viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


@api_view(["POST"])
def update_bus_location(request, bus_id):

    try:

        bus = Bus.objects.get(id=bus_id)

        lat = request.data.get("lat")
        lng = request.data.get("lng")
        speed = request.data.get("speed", 0)

        bus.current_lat = lat
        bus.current_lng = lng
        bus.speed = speed

        bus.save()

        BusLocation.objects.create(
            bus=bus,
            latitude=lat,
            longitude=lng,
            speed=speed
        )

        return Response({
            "message": "GPS updated successfully",
            "bus_id": bus.id,
            "lat": lat,
            "lng": lng,
            "speed": speed
        })

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)
    

class PassengerViewSet(viewsets.ModelViewSet):

    queryset = Passenger.objects.all()

    serializer_class = PassengerSerializer