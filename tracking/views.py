from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Route, Stop, Bus
from .serializers import RouteSerializer, StopSerializer, BusSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class StopViewSet(viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        bus = self.get_object()

        # Get all stops for this route in order
        stops = Stop.objects.filter(route=bus.route).order_by('order')

        if not stops.exists():
            return Response({"error": "No stops for this route"})

        # Move to next stop (loop back to start)
        bus.current_stop_index = (bus.current_stop_index + 1) % len(stops)

        next_stop = stops[bus.current_stop_index]

        # Update bus location
        bus.current_lat = next_stop.latitude
        bus.current_lng = next_stop.longitude

        bus.save()

        return Response({
            "message": "Bus moved",
            "bus_id": bus.id,
            "current_stop": next_stop.name,
            "current_stop_index": bus.current_stop_index,
            "lat": bus.current_lat,
            "lng": bus.current_lng
        })