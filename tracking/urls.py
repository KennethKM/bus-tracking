from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    home,
    passenger_portal,
    passenger_profile,
    RouteViewSet,
    StopViewSet,
    BusViewSet,
    PassengerViewSet,
    DriverViewSet,
    update_bus_location,
    update_passenger_location,
    nearby_passengers,
    bus_eta,
    nearby_buses,
    assign_driver_bus,
    update_driver_location_view,
    driver_interface,
)



router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', StopViewSet)
router.register(r'buses', BusViewSet)
router.register(r'passengers', PassengerViewSet)
router.register(r'drivers', DriverViewSet)


urlpatterns = [

    path('', home, name='home'),

    path(
        'buses/<int:bus_id>/location/',
        update_bus_location
    ),

    path(
    'passengers/<int:passenger_id>/location/',
    update_passenger_location
    ),

    path(
    'buses/<int:bus_id>/nearby-passengers/',
    nearby_passengers
    ),

    path(
    'buses/<int:bus_id>/eta/<int:passenger_id>/',
    bus_eta
    ),

    path(
    'passengers/<int:passenger_id>/nearby-buses/',
    nearby_buses
    ),

    path(
        'drivers/<int:driver_id>/assign-bus/',
        assign_driver_bus,
        name='assign_driver_bus'
    ),

    path(
        'drivers/<int:driver_id>/location/',
        update_driver_location_view,
        name='update_driver_location'
    ),

    path(
        'drivers/<int:driver_id>/start-trip/',
        # start trip endpoint
        # implemented in views.start_trip_view
        # name: start_trip
        __import__('tracking.views', fromlist=['start_trip_view']).start_trip_view,
        name='start_trip'
    ),

    path(
        'drivers/<int:driver_id>/stop-trip/',
        # stop trip endpoint
        # implemented in views.stop_trip_view
        # name: stop_trip
        __import__('tracking.views', fromlist=['stop_trip_view']).stop_trip_view,
        name='stop_trip'
    ),

    path(
        'buses/<int:bus_id>/stop-status/',
        __import__('tracking.views', fromlist=['bus_stop_status']).bus_stop_status,
        name='bus_stop_status'
    ),

    # Dev-only auto-login shortcut (only active when DEBUG=True)
    path(
        'dev/login-admin/',
        __import__('tracking.views', fromlist=['dev_auto_login_admin']).dev_auto_login_admin,
        name='dev_auto_login_admin'
    ),

    path(
        'drivers/<int:driver_id>/interface/',
        driver_interface,
        name='driver_interface'
    ),

    path(
        'passenger/portal/',
        passenger_portal,
        name='passenger_portal'
    ),

    path(
        'passenger/<int:passenger_id>/',
        passenger_profile,
        name='passenger_profile'
    ),

] + router.urls
