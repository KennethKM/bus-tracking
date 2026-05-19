from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RouteViewSet,
    StopViewSet,
    BusViewSet,
    PassengerViewSet,
    update_bus_location
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

] + router.urls