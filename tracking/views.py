from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404




from .models import (
    Route,
    Stop,
    Bus,
    Passenger,
    WaitingRequest,
    Trip,
    StopTime
)


from .serializers import (
    RouteSerializer,
    RouteSearchSerializer,
    StartTripSerializer,
    StopSerializer,
    BusSerializer,
    PassengerSerializer,
    WaitingRequestSerializer,
    DriverSessionSerializer,
    
)


from .services.location_service import (
    save_bus_location,
    
)


from .services.route_service import (
get_nearby_passengers
)


from .services.eta_service import (
    calculate_eta
)


from .services.waiting_request_service import (
    get_waiting_count,
    get_route_waiting_overview,
    mark_as_boarded
)

from tracking.services.trip_service import (
    
    start_trip
)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().order_by("route_long_name")
    serializer_class = RouteSerializer


class StopViewSet(viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


class PassengerViewSet(viewsets.ModelViewSet):

    queryset = Passenger.objects.all()

    serializer_class = PassengerSerializer


class WaitingRequestViewSet(viewsets.ModelViewSet):

    queryset = WaitingRequest.objects.all()

    serializer_class = WaitingRequestSerializer

@api_view(["GET"])
def driver_session(request, registration_number):

    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    serializer = DriverSessionSerializer(bus)

    return Response(serializer.data)


@api_view(["POST"])
def activate_bus(request, registration_number):

    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    bus.activate()

    return Response(
        {
            "message": "Bus activated successfully."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
def deactivate_bus(request, registration_number):

    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    bus.deactivate()

    return Response(
        {
            "message": "Bus deactivated successfully."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
def start_fresh(request, registration_number):

    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    bus.start_fresh()

    return Response(
        {
            "message": "Operational state reset successfully."
        },
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
def route_destinations(request, route_id):

    route = get_object_or_404(
        Route,
        route_id=route_id
    )

    destinations = set()

    trips = Trip.objects.filter(route=route)

    for trip in trips:

        last_stop = (
            StopTime.objects
            .filter(trip=trip)
            .select_related("stop")
            .order_by("-stop_sequence")
            .first()
        )

        if last_stop:
            destinations.add(
                last_stop.stop.stop_name
            )

    return Response(
        [
            {
                "destination": destination
            }
            for destination in sorted(destinations)
        ]
    )


@api_view(["GET"])
def search_routes(request):

    query = request.GET.get("q", "").strip()

    routes = Route.objects.all()

    if query:

        routes = routes.filter(
            route_long_name__icontains=query
        )

    serializer = RouteSearchSerializer(
        routes,
        many=True
    )

    return Response(serializer.data)



@api_view(["POST"])
def start_trip_view(request):

    serializer = StartTripSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    bus = start_trip(
        registration_number=serializer.validated_data["registration_number"],
        route_id=serializer.validated_data["route_id"],
        destination=serializer.validated_data["destination"],
    )

    return Response(
        {
            "message": "Trip started successfully.",
            "registration_number": bus.registration_number,
            "trip_id": bus.current_trip.trip_id,
            "current_stop": bus.current_stop_time.stop.stop_name,
            "status": bus.status,
        },
        status=status.HTTP_200_OK,
    )




@api_view(["POST"])
def update_bus_location(request, registration_number):

    try:

        bus = save_bus_location(
            registration_number,
            request.data.get("lat"),
            request.data.get("lng"),
            request.data.get("speed", 0)
        )

        return Response({
            "message": "GPS updated successfully",
            "registration_number": bus.registration_number,
            "lat": bus.current_lat,
            "lng": bus.current_lng,
            "speed": bus.speed,
            "status": bus.status
        })

    except Bus.DoesNotExist:

        return Response(
            {"error": "Bus not found"},
            status=404
        )
    




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
def bus_eta(request, bus_id, stop_id):

    try:

        bus = Bus.objects.get(id=bus_id)
        stop = Stop.objects.get(stop_id=stop_id)

        eta_minutes = calculate_eta(
            bus,
            stop
        )

        return Response({
            "bus_id": bus.id,
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "eta_minutes": eta_minutes
        })

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)

    except Stop.DoesNotExist:

        return Response({
            "error": "Stop not found"
        }, status=404)







@api_view(["GET"])
def waiting_count(request, route_id, stop_id):

    try:

        route = Route.objects.get(id=route_id)

        stop = Stop.objects.get(id=stop_id)

        count = get_waiting_count(
            route_id,
            stop_id
        )

        return Response({
            "route_name": route.name,
            "stop_name": stop.name,
            "waiting_count": count
        })

    except Route.DoesNotExist:

        return Response({
            "error": "Route not found"
        }, status=404)

    except Stop.DoesNotExist:

        return Response({
            "error": "Stop not found"
        }, status=404)




@api_view(["GET"])
def route_waiting_overview(request, bus_id):

    try:

        overview = get_route_waiting_overview(
            bus_id
        )

        return Response(overview)

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)
    

@api_view(["POST"])
def board_passenger(request, waiting_request_id):

    try:

        waiting_request = mark_as_boarded(
            waiting_request_id
        )

        return Response({
            "message": "Passenger boarded",
            "waiting_request_id": waiting_request.id,
            "status": waiting_request.status
        })

    except WaitingRequest.DoesNotExist:

        return Response({
            "error": "Waiting request not found"
        }, status=404)





















