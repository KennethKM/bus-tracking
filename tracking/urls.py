from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RouteViewSet,
    StopViewSet,
    BusViewSet,
    PassengerViewSet,
    update_bus_location,
    update_passenger_location,
    nearby_passengers,
    bus_eta,
    nearby_buses
)



router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', StopViewSet)
router.register(r'buses', BusViewSet)
router.register(r'passengers', PassengerViewSet)


urlpatterns = [

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

] + router.urls