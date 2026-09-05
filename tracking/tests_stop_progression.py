from django.test import TestCase
from rest_framework.test import APIClient
from .models import Route, Stop, Bus, Driver
from .services.stop_progression_service import advance_bus_stop_progress
from .services.location_service import save_bus_location


class StopProgressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.route = Route.objects.create(name='P')

    def _make_stop(self, order, lat, lng, name=None):
        return Stop.objects.create(route=self.route, name=(name or f'S{order}'), latitude=lat, longitude=lng, order=order)

    def test_active_bus_reaches_next_stop_advances(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        # place bus near stop1 within threshold
        bus.current_lat = 0.0005
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 1)

    def test_active_bus_not_near_next_no_change(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.01, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        # far from stop1
        bus.current_lat = 0.001
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    def test_inactive_bus_does_not_advance(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=False)
        bus.current_lat = 0.0005
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    def test_final_stop_no_change(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0005, current_lng=0.0, speed=0, current_stop_index=1, is_active=True)
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 1)

    def test_single_stop_route_never_advances(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        bus.current_lat = 0.0
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    def test_missing_gps_no_change(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        # simulate missing/invalid GPS using prototype 0,0 which detection treats as invalid
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    def test_invalid_gps_no_change(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        # use out-of-range latitude to simulate invalid GPS (detection will reject)
        bus = Bus.objects.create(route=self.route, current_lat=999.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    # Note: Bus.route is non-nullable in models; 'no route' case is covered by
    # test_no_stops_no_change which creates a route with zero stops.

    def test_no_stops_no_change(self):
        other_route = Route.objects.create(name='Empty')
        bus = Bus.objects.create(route=other_route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)

    def test_no_backward_movement(self):
        # create three stops
        s0 = self._make_stop(1, -0.002, 0.0)
        s1 = self._make_stop(2, -0.001, 0.0)
        s2 = self._make_stop(3, 0.0, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=2, is_active=True)
        # GPS near earlier stop s1
        bus.current_lat = -0.001
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 2)

    def test_no_skipping(self):
        # stops at indices 0,1,2,3
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        s2 = self._make_stop(3, 0.001, 0.0)
        s3 = self._make_stop(4, 0.002, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=1, is_active=True)
        # GPS near stop 3 (index 3) but not near stop 2
        bus.current_lat = 0.0019
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        # should not jump to index 3
        self.assertEqual(bus.current_stop_index, 1)

    def test_exact_one_step_progression(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        s2 = self._make_stop(3, 0.001, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=1, is_active=True)
        # GPS reaches stop 2
        bus.current_lat = 0.001
        bus.current_lng = 0.0
        bus.save()
        advance_bus_stop_progress(bus)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 2)

    def test_integration_location_update_advances_when_active(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=True)
        url = f'/buses/{bus.id}/location/'
        res = self.client.post(url, data={"lat": 0.0005, "lng": 0.0, "speed": 0}, format='json')
        self.assertEqual(res.status_code, 200)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 1)

    def test_integration_location_update_does_not_advance_when_inactive(self):
        s0 = self._make_stop(1, 0.0, 0.0)
        s1 = self._make_stop(2, 0.0005, 0.0)
        bus = Bus.objects.create(route=self.route, current_lat=0.0, current_lng=0.0, speed=0, current_stop_index=0, is_active=False)
        url = f'/buses/{bus.id}/location/'
        res = self.client.post(url, data={"lat": 0.0005, "lng": 0.0, "speed": 0}, format='json')
        self.assertEqual(res.status_code, 200)
        bus.refresh_from_db()
        self.assertEqual(bus.current_stop_index, 0)
