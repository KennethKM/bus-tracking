from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


from .models import (
    Route,
    Stop,
    Bus,
    Passenger,
    WaitingRequest,
    Trip,
    StopTime,
    Driver,
    DriverBusAssignment,
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




from .services.eta_service import (
    calculate_eta
)


from .services.waiting_request_service import (
    get_waiting_count,
    get_route_waiting_overview,
    mark_as_boarded,
    cancel_waiting_request,
    complete_waiting_request,
    expire_waiting_request,
)


from tracking.services.trip_service import (
    start_trip,
    get_trip_for_route_and_destination
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
    serializer_class = WaitingRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WaitingRequest.objects.filter(
            passenger=self.request.user.passenger_profile
        )

    def perform_create(self, serializer):
        passenger = self.request.user.passenger_profile

        if WaitingRequest.objects.filter(
            passenger=passenger,
            status__in=["WAITING", "ON_BOARD"]
        ).exists():
            raise serializers.ValidationError({
                "passenger": "You already have an active waiting request."
            })

        serializer.save(passenger=passenger)


def get_authorized_bus_for_driver(request, registration_number):
    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    if not hasattr(request.user, "driver_profile"):
        return None, Response(
            {"error": "This account is not a driver account."},
            status=status.HTTP_403_FORBIDDEN
        )

    driver = request.user.driver_profile

    if not driver.is_active:
        return None, Response(
            {"error": "This driver account is inactive."},
            status=status.HTTP_403_FORBIDDEN
        )

    assignment_exists = DriverBusAssignment.objects.filter(
        driver=driver,
        bus=bus,
        is_active=True
    ).exists()

    if not assignment_exists:
        return None, Response(
            {"error": "You are not authorized to operate this bus."},
            status=status.HTTP_403_FORBIDDEN
        )

    return bus, None



@api_view(["POST"])
def register_passenger(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    name = request.data.get("name", "").strip()
    email = request.data.get("email", "").strip()

    if not username or not password or not name:
        return Response(
            {"error": "Username, password, and name are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )

    Passenger.objects.create(
        user=user,
        name=name
    )

    return Response(
        {
            "message": "Passenger account created successfully.",
            "username": user.username,
            "name": name
        },
        status=status.HTTP_201_CREATED
    )



@api_view(["GET"])
def driver_session(request, registration_number):

    bus = get_object_or_404(
        Bus,
        registration_number=registration_number
    )

    serializer = DriverSessionSerializer(bus)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def activate_bus(request, registration_number):

    bus, authorization_error = get_authorized_bus_for_driver(
        request,
        registration_number
    )

    if authorization_error:
        return authorization_error

    bus.activate()

    return Response(
        {
            "message": "Bus activated successfully."
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_bus(request, registration_number):

    bus, authorization_error = get_authorized_bus_for_driver(
        request,
        registration_number
    )

    if authorization_error:
        return authorization_error

    bus.deactivate()

    return Response(
        {
            "message": "Bus deactivated successfully."
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_fresh(request, registration_number):

    bus, authorization_error = get_authorized_bus_for_driver(
        request,
        registration_number
    )

    if authorization_error:
        return authorization_error

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
def trip_stops(request, route_id):

    destination = request.GET.get(
        "destination",
        ""
    ).strip()

    if not destination:
        return Response(
            {"error": "Destination is required."},
            status=400
        )

    route = get_object_or_404(
        Route,
        route_id=route_id
    )

    trip = get_trip_for_route_and_destination(
        route,
        destination,
    )

    if trip is None:
        return Response(
            {
                "error": (
                    "No trip ends at the selected destination."
                )
            },
            status=404
        )

    stop_times = (
        StopTime.objects
        .filter(trip=trip)
        .select_related("stop")
        .order_by("stop_sequence")
    )

    return Response({
        "trip_id": trip.trip_id,
        "route_id": route.route_id,
        "destination": destination,
        "stops": [
            {
                "stop_id": stop_time.stop.stop_id,
                "stop_name": stop_time.stop.stop_name,
                "stop_sequence": stop_time.stop_sequence,
            }
            for stop_time in stop_times
        ]

    })










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
@permission_classes([IsAuthenticated])
def start_trip_view(request):

    serializer = StartTripSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    registration_number = serializer.validated_data[
        "registration_number"
    ]

    _, authorization_error = get_authorized_bus_for_driver(
        request,
        registration_number
    )

    if authorization_error:
        return authorization_error

    bus = start_trip(
        registration_number=registration_number,
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
@permission_classes([IsAuthenticated])
def update_bus_location(request, registration_number):

    _, authorization_error = get_authorized_bus_for_driver(
        request,
        registration_number
    )

    if authorization_error:
        return authorization_error

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
            status=status.HTTP_404_NOT_FOUND
        )
    








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
def waiting_count(request, trip_id, stop_id):

    try:
        trip = Trip.objects.select_related("route").get(
            trip_id=trip_id
        )

        stop = Stop.objects.get(
            stop_id=stop_id
        )

        stop_on_trip = StopTime.objects.filter(
            trip=trip,
            stop=stop
        ).exists()

        if not stop_on_trip:
            return Response(
                {"error": "Stop is not served by this trip."},
                status=400
            )

        count = get_waiting_count(
            trip_id,
            stop_id
        )

        return Response({
            "trip_id": trip.trip_id,
            "route_id": trip.route.route_id,
            "route_name": trip.route.route_long_name,
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "waiting_count": count
        })

    except Trip.DoesNotExist:
        return Response(
            {"error": "Trip not found"},
            status=404
        )

    except Stop.DoesNotExist:
        return Response(
            {"error": "Stop not found"},
            status=404
        )



@api_view(["GET"])
def route_waiting_overview(request, registration_number):

    try:

        overview = get_route_waiting_overview(
            registration_number
        )

        return Response(overview)

    except Bus.DoesNotExist:

        return Response({
            "error": "Bus not found"
        }, status=404)




@api_view(["POST"])
def login_passenger(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not hasattr(user, "passenger_profile"):
        return Response(
            {"error": "This account is not a passenger account."},
            status=status.HTTP_403_FORBIDDEN
        )

    login(request, user)

    passenger = user.passenger_profile

    return Response({
        "message": "Login successful.",
        "passenger": {
            "id": passenger.id,
            "name": passenger.name,
            "username": user.username,
            "email": user.email,
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_passenger(request):
    if not hasattr(request.user, "passenger_profile"):
        return Response(
            {"error": "This account is not a passenger account."},
            status=status.HTTP_403_FORBIDDEN
        )

    passenger = request.user.passenger_profile

    return Response({
        "passenger": {
            "id": passenger.id,
            "name": passenger.name,
            "username": request.user.username,
            "email": request.user.email,
        }
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_passenger(request):
    logout(request)

    return Response({
        "message": "Logout successful."
    })

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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_waiting_request_view(request, waiting_request_id):
    passenger = request.user.passenger_profile

    try:
        waiting_request = cancel_waiting_request(
            waiting_request_id,
            passenger
        )

        return Response({
            "message": "Waiting request cancelled.",
            "waiting_request_id": waiting_request.id,
            "status": waiting_request.status
        })

    except WaitingRequest.DoesNotExist:
        return Response({
            "error": "Active waiting request not found."
        }, status=status.HTTP_404_NOT_FOUND)



@api_view(["POST"])
def login_driver(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not hasattr(user, "driver_profile"):
        return Response(
            {"error": "This account is not a driver account."},
            status=status.HTTP_403_FORBIDDEN
        )

    driver = user.driver_profile

    if not driver.is_active:
        return Response(
            {"error": "This driver account is inactive."},
            status=status.HTTP_403_FORBIDDEN
        )

    login(request, user)

    return Response({
        "message": "Driver login successful.",
        "driver": {
            "id": driver.id,
            "name": user.get_full_name().strip() or user.username,
            "username": user.username,
            "email": user.email,
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_driver(request):
    if not hasattr(request.user, "driver_profile"):
        return Response(
            {"error": "This account is not a driver account."},
            status=status.HTTP_403_FORBIDDEN
        )

    driver = request.user.driver_profile

    if not driver.is_active:
        return Response(
            {"error": "This driver account is inactive."},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response({
        "driver": {
            "id": driver.id,
            "name": request.user.get_full_name().strip() or request.user.username,
            "username": request.user.username,
            "email": request.user.email,
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def driver_assigned_buses(request):
    if not hasattr(request.user, "driver_profile"):
        return Response(
            {"error": "This account is not a driver account."},
            status=status.HTTP_403_FORBIDDEN
        )

    driver = request.user.driver_profile

    if not driver.is_active:
        return Response(
            {"error": "This driver account is inactive."},
            status=status.HTTP_403_FORBIDDEN
        )

    assignments = (
        DriverBusAssignment.objects
        .filter(
            driver=driver,
            is_active=True
        )
        .select_related("bus")
        .order_by("bus__registration_number")
    )

    return Response({
        "driver_id": driver.id,
        "buses": [
            {
                "id": assignment.bus.id,
                "registration_number": assignment.bus.registration_number,
                "status": assignment.bus.status,
                "is_active": assignment.bus.is_active,
            }
            for assignment in assignments
        ]
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_driver(request):
    if not hasattr(request.user, "driver_profile"):
        return Response(
            {"error": "This account is not a driver account."},
            status=status.HTTP_403_FORBIDDEN
        )

    logout(request)

    return Response({
        "message": "Driver logout successful."
    })




@api_view(["POST"])
def complete_waiting_request_view(request, waiting_request_id):
    try:
        waiting_request = complete_waiting_request(
            waiting_request_id
        )

        return Response({
            "message": "Passenger trip completed.",
            "waiting_request_id": waiting_request.id,
            "status": waiting_request.status
        })

    except WaitingRequest.DoesNotExist:
        return Response({
            "error": "On-board waiting request not found."
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def expire_waiting_request_view(request, waiting_request_id):
    try:
        waiting_request = expire_waiting_request(
            waiting_request_id
        )

        return Response({
            "message": "Waiting request expired.",
            "waiting_request_id": waiting_request.id,
            "status": waiting_request.status
        })

    except WaitingRequest.DoesNotExist:
        return Response({
            "error": "Active waiting request not found."
        }, status=status.HTTP_404_NOT_FOUND)


















