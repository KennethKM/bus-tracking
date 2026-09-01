from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RouteViewSet,
    StopViewSet,
    BusViewSet,
    PassengerViewSet,
    WaitingRequestViewSet,
    
    route_destinations, 
    search_routes,
    driver_session,
    activate_bus,
    deactivate_bus,
    start_fresh,
    update_bus_location,
    nearby_passengers,
    bus_eta,
    start_trip_view,
    waiting_count,
    route_waiting_overview,
    board_passenger
)

router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', StopViewSet)
router.register(r'buses', BusViewSet)
router.register(r'passengers', PassengerViewSet)
router.register(r'waiting-requests', WaitingRequestViewSet)


urlpatterns = [
   path(
    "buses/start-trip/",
    start_trip_view,
    name="start-trip",
    ),

   
   
   path(
    "routes/search/",
    search_routes,
    name="search_routes",
    ),

    path(
    "buses/<str:registration_number>/location/",
    update_bus_location
    ),

    path(
        'buses/<int:bus_id>/nearby-passengers/',
        nearby_passengers
    ),

    path(
    'buses/<int:bus_id>/eta/<int:stop_id>/',
    bus_eta
    ),



    path(
        'routes/<int:route_id>/stops/<int:stop_id>/waiting-count/',
        waiting_count
    ),

    path(
        'buses/<int:bus_id>/waiting-overview/',
        route_waiting_overview
    ),

    path(
        'waiting-requests/<int:waiting_request_id>/board/',
        board_passenger
    ),

     path(
    "buses/<str:registration_number>/driver-session/",
    driver_session
    ),

    path(
        "buses/<str:registration_number>/activate/",
        activate_bus
    ),

    path(
        "buses/<str:registration_number>/deactivate/",
        deactivate_bus
    ),

    path(
        "buses/<str:registration_number>/start-fresh/",
        start_fresh
    ),

    path(
    "routes/<str:route_id>/destinations/",
    route_destinations,
    name="route_destinations",
    ),

] + router.urls