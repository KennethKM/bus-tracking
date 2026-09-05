from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Route, Stop, Bus, Driver

class StopStatusEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.route = Route.objects.create(name='RouteX')

    def _make_stop(self, order, lat, lng, name=None):
        return Stop.objects.create(route=self.route, name=(name or f'S{order}'), latitude=lat, longitude=lng, order=order)

    def test_stop_status_returns_stops_and_distances(self):
        s0 = self._make_stop(1, 0.0, 0.0, 'A')
        s1 = self._make_stop(2, 0.001, 0.0, 'B')
        # avoid the prototype 0,0 invalid coordinate rule by using a tiny offset
        bus = Bus.objects.create(route=self.route, current_lat=0.00001, current_lng=0.0, speed=0, current_stop_index=0)
        url = f'/buses/{bus.id}/stop-status/'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['bus_id'], bus.id)
        # current_stop should be present and have id/name
        self.assertIsNotNone(data.get('current_stop'))
        self.assertIsInstance(data.get('distance_to_current_m'), (float, type(None)))

    def test_endpoint_does_not_modify_bus_index(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0)
        orig = bus.current_stop_index
        url = f'/buses/{bus.id}/stop-status/'
        _ = self.client.get(url)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, orig)

    def test_invalid_gps_returns_nulls(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0)
        url = f'/buses/{bus.id}/stop-status/'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNone(data.get('current_stop'))
        self.assertIsNone(data.get('next_stop'))

    def test_final_stop_next_null(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.001, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.001, current_lng=0.0, speed=0, current_stop_index=1)
        url = f'/buses/{bus.id}/stop-status/'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # may return current_stop if within threshold; next_stop should be None since final
        self.assertIsNone(data.get('next_stop'))

    def test_driver_interface_includes_stop_info(self):
        s0 = self._make_stop(1, 0.0, 0.0, 'Start')
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0)
        driver = Driver.objects.create(name='Drv', assigned_bus=bus)
        res = self.client.get(reverse('driver_interface', args=[driver.id]))
        self.assertEqual(res.status_code, 200)
        # page should include the Route Progress header
        self.assertIn('Route Progress', res.content.decode())

