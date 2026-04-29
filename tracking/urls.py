from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouteViewSet, StopViewSet, BusViewSet

router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', StopViewSet)
router.register(r'buses', BusViewSet)

urlpatterns = router.urls