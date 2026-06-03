from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Route, Stop, Bus, BusLocation, Passenger

from .services.location_service import (
    save_bus_location,
    save_passenger_location
)


from .services.route_service import (
get_nearby_buses,
get_nearby_passengers
)


from .services.eta_service import (
    
    get_bus_eta
)


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

        bus = save_bus_location(
            bus_id,
            request.data.get("lat"),
            request.data.get("lng"),
            request.data.get("speed", 0)
        )

        return Response({
            "message": "GPS updated successfully",
            "bus_id": bus.id,
            "lat": bus.current_lat,
            "lng": bus.current_lng,
            "speed": bus.speed
        })

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)
    


@api_view(["POST"])
def update_passenger_location(request, passenger_id):

    try:

        passenger = save_passenger_location(
            passenger_id,
            request.data.get("lat"),
            request.data.get("lng"),
            request.data.get("is_active", False)
        )

        return Response({
            "message": "Passenger updated successfully",
            "passenger_id": passenger.id,
            "lat": passenger.latitude,
            "lng": passenger.longitude,
            "is_active": passenger.is_active
        })

    except Passenger.DoesNotExist:

        return Response({
            "error": "Passenger not found"
        }, status=404)



@api_view(["GET"])
def nearby_passengers(request, bus_id):

    try:

        bus = Bus.objects.get(id=bus_id)

        nearby = get_nearby_passengers(
            bus
        )

        return Response({
            "bus_id": bus.id,
            "nearby_passengers": nearby
        })

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)



@api_view(["GET"])
def bus_eta(request, bus_id, passenger_id):

    try:

        bus = Bus.objects.get(id=bus_id)

        passenger = Passenger.objects.get(id=passenger_id)

        result = get_bus_eta(
            bus,
            passenger
        )

        return Response(result)

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)

    except Passenger.DoesNotExist:

        return Response({
            "error": "Passenger not found"
        }, status=404)





@api_view(["GET"])
def nearby_buses(request, passenger_id):

    try:
        passenger = Passenger.objects.get(id=passenger_id)

        results = get_nearby_buses(passenger)

        return Response({
            "passenger_id": passenger.id,
            "nearby_buses": results
        })

    except Passenger.DoesNotExist:

        return Response({
            "error": "Passenger not found"
        }, status=404)


class PassengerViewSet(viewsets.ModelViewSet):

    queryset = Passenger.objects.all()

    serializer_class = PassengerSerializer