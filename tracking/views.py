from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Route, Stop, Bus, BusLocation, Passenger, Driver

from .services.location_service import (
    save_bus_location,
    save_passenger_location,
    assign_driver_to_bus,
    update_driver_location
)
from .services.trip_service import (
    start_trip_for_driver,
    stop_trip_for_driver,
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
    PassengerSerializer,
    DriverSerializer,
    LocationSerializer
)
from .services.stop_detection_service import determine_current_and_next_stop




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

    # validate payload
    serializer = LocationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Invalid payload", "details": serializer.errors}, status=400)

    lat = serializer.validated_data.get('lat')
    lng = serializer.validated_data.get('lng')
    speed = serializer.validated_data.get('speed', 0)

    try:
        bus = save_bus_location(bus_id, lat, lng, speed)

        return Response({
            "message": "GPS updated successfully",
            "bus_id": bus.id,
            "lat": bus.current_lat,
            "lng": bus.current_lng,
            "speed": bus.speed
        })

    except Bus.DoesNotExist:
        return Response({"error": "Bus not found"}, status=404)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    


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


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


def home(request):
    return render(request, "tracking/home.html")


def passenger_portal(request):
    """Simple passenger-facing portal with signup and login.

    Signup flow (POST with `action=signup`): creates a Passenger and
    redirects to the passenger profile. Login flow (POST with
    `action=login`) looks up an existing Passenger by name and redirects.
    This is intentionally minimal for the prototype.
    """
    message = None
    error = None

    if request.method == "POST":
        action = request.POST.get("action")
        name = request.POST.get("name", "").strip()

        if not name:
            error = "Please provide a name."
        else:
            if action == "signup":
                passenger = Passenger.objects.create(
                    name=name,
                    latitude=0.0,
                    longitude=0.0,
                    is_active=False,
                )
                return redirect("passenger_profile", passenger_id=passenger.id)

            elif action == "login":
                passenger = Passenger.objects.filter(name=name).first()
                if passenger:
                    return redirect("passenger_profile", passenger_id=passenger.id)
                else:
                    error = "Passenger not found. Please sign up."

            else:
                error = "Unknown action"

    return render(request, "tracking/passenger_portal.html", {"message": message, "error": error})


def passenger_profile(request, passenger_id):
    passenger = get_object_or_404(Passenger, id=passenger_id)
    return render(request, "tracking/passenger_profile.html", {"passenger": passenger})


def driver_interface(request, driver_id):
    driver = Driver.objects.filter(id=driver_id).first()
    bus = driver.assigned_bus if driver else None
    nearby_passengers = []
    active_passenger_count = 0
    current_stop = None
    status_message = None
    error_message = None

    if not driver:
        driver = Driver(id=driver_id, name=f"Driver {driver_id}", is_active=True)

    if request.method == "POST":
        try:
            lat = float(request.POST.get("lat", 0))
            lng = float(request.POST.get("lng", 0))
            speed = float(request.POST.get("speed", 0))
            if driver.pk and driver.assigned_bus:
                bus = update_driver_location(driver_id, lat, lng, speed)
                status_message = "Bus location updated successfully."
            else:
                error_message = "Assign a bus to this driver before publishing location."
        except (TypeError, ValueError) as exc:
            error_message = str(exc) or "Please enter valid coordinates."

    if bus:
        nearby_passengers = get_nearby_passengers(bus)
        active_passenger_count = len(nearby_passengers)
        route_stops = Stop.objects.filter(route=bus.route).order_by('order')
        if bus.current_stop_index < len(route_stops):
            # default current_stop from stored index (used as a fallback)
            current_stop = route_stops[bus.current_stop_index]

        # read-only detection of current/next stop to display
        try:
            det = determine_current_and_next_stop(bus) or {}
            # override current_stop with detected value (may be None)
            current_stop = det.get('current_stop')
            next_stop = det.get('next_stop')
            distance_to_current_m = det.get('distance_to_current_m')
            distance_to_next_m = det.get('distance_to_next_m')
            candidate_index = det.get('candidate_index')
        except Exception:
            next_stop = None
            distance_to_current_m = None
            distance_to_next_m = None
            candidate_index = None

    return render(
        request,
        "tracking/driver_interface.html",
        {
            "driver": driver,
            "bus": bus,
            "route": bus.route if bus else None,
            "nearby_passengers": nearby_passengers,
            "active_passenger_count": active_passenger_count,
            "current_stop": current_stop,
            "next_stop": next_stop if bus else None,
            "distance_to_current_m": distance_to_current_m if bus else None,
            "distance_to_next_m": distance_to_next_m if bus else None,
            "stop_candidate_index": candidate_index if bus else None,
            "status_message": status_message,
            "error_message": error_message,
            "publish_url": reverse('update_driver_location', args=[driver_id]),
            "can_publish": bool(driver and getattr(driver, 'assigned_bus', None)),
        },
    )


def dev_auto_login_admin(request):
    """Dev-only helper: create or get a local dev superuser and log in.

    Only available when `DEBUG` is True. Redirects to the admin index.
    """
    if not getattr(settings, 'DEBUG', False):
        return HttpResponseForbidden('Dev auto-login disabled')

    User = get_user_model()
    username = 'Madalitso Nyirenda'
    password = 'Prototype'
    user, created = User.objects.get_or_create(username=username, defaults={'email': 'madalitsoanyirenda@gmail.com'})
    if created:
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

    # ensure it's a superuser/staff in case it existed
    if not (user.is_active and user.is_staff and user.is_superuser):
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

    # log the user in and redirect to admin
    auth_login(request, user)
    return redirect('/admin/')


@api_view(["POST"])
def assign_driver_bus(request, driver_id):
    try:
        driver = assign_driver_to_bus(
            driver_id,
            request.data.get("bus_id")
        )

        return Response({
            "message": "Driver assigned to bus successfully",
            "driver_id": driver.id,
            "assigned_bus_id": driver.assigned_bus.id if driver.assigned_bus else None
        })

    except Driver.DoesNotExist:
        return Response({
            "error": "Driver not found"
        }, status=404)

    except Bus.DoesNotExist:
        return Response({
            "error": "Bus not found"
        }, status=404)



@api_view(["POST"])
def start_trip_view(request, driver_id):
    try:
        result = start_trip_for_driver(driver_id)
        return Response({
            "message": "Trip started",
            **result
        })
    except Driver.DoesNotExist:
        return Response({"error": "Driver not found"}, status=404)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["POST"])
def stop_trip_view(request, driver_id):
    try:
        result = stop_trip_for_driver(driver_id)
        return Response({
            "message": "Trip stopped",
            **result
        })
    except Driver.DoesNotExist:
        return Response({"error": "Driver not found"}, status=404)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["GET"])
def bus_stop_status(request, bus_id):
    try:
        bus = Bus.objects.get(id=bus_id)

        det = determine_current_and_next_stop(bus) or {}

        def stop_to_dict(s):
            if not s:
                return None
            return {"id": s.id, "name": s.name, "order": s.order}

        return Response({
            "bus_id": bus.id,
            "current_stop": stop_to_dict(det.get('current_stop')),
            "next_stop": stop_to_dict(det.get('next_stop')),
            "distance_to_current_m": det.get('distance_to_current_m'),
            "distance_to_next_m": det.get('distance_to_next_m'),
            "candidate_index": det.get('candidate_index')
        })

    except Bus.DoesNotExist:
        return Response({"error": "Bus not found"}, status=404)
    except Exception:
        return Response({
            "error": "Failed to determine stop status"
        }, status=500)


@api_view(["POST"])
def update_driver_location_view(request, driver_id):
    # validate payload
    serializer = LocationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": "Invalid payload", "details": serializer.errors}, status=400)

    lat = serializer.validated_data.get('lat')
    lng = serializer.validated_data.get('lng')
    speed = serializer.validated_data.get('speed', 0)

    try:
        bus = update_driver_location(driver_id, lat, lng, speed)

        return Response({
            "message": "Driver location updated successfully",
            "driver_id": driver_id,
            "bus_id": bus.id,
            "lat": bus.current_lat,
            "lng": bus.current_lng,
            "speed": bus.speed
        })

    except Driver.DoesNotExist:
        return Response({"error": "Driver not found"}, status=404)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Bus.DoesNotExist:
        return Response({"error": "Assigned bus not found"}, status=404)
