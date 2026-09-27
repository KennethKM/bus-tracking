from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Driver, Bus, Route, RouteRequest


class TripEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.route = Route.objects.create(name='Test Route', origin='A', destination='B')
        self.bus = Bus.objects.create(route=self.route, registration_number='TEST123', capacity=20, current_lat=0.1, current_lng=0.1)
        self.driver = Driver.objects.create(name='Test Driver', assigned_bus=self.bus)

    def test_start_trip_sets_bus_active(self):
        url = f"/api/drivers/{self.driver.id}/start-trip/"
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.bus.refresh_from_db()
        self.assertTrue(self.bus.is_active)
        self.assertIn('message', res.json())

    def test_start_trip_resets_stale_stop_index(self):
        self.bus.current_stop_index = 17
        self.bus.save(update_fields=['current_stop_index'])
        url = f"/api/drivers/{self.driver.id}/start-trip/"
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.current_stop_index, 0)
        self.assertTrue(self.bus.is_active)
        self.assertEqual(res.json().get('current_stop_index'), 0)

    def test_stop_trip_sets_bus_inactive(self):
        # start first
        start_url = f"/api/drivers/{self.driver.id}/start-trip/"
        self.client.post(start_url)
        stop_url = f"/api/drivers/{self.driver.id}/stop-trip/"
        res = self.client.post(stop_url)
        self.assertEqual(res.status_code, 200)
        self.bus.refresh_from_db()
        self.assertFalse(self.bus.is_active)

    def test_start_trip_no_bus_assigned(self):
        d = Driver.objects.create(name='No Bus')
        url = f"/api/drivers/{d.id}/start-trip/"
        res = self.client.post(url)
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

    def test_stop_trip_no_bus_assigned(self):
        d = Driver.objects.create(name='No Bus')
        url = f"/api/drivers/{d.id}/stop-trip/"
        res = self.client.post(url)
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

    def _make_approved(self, driver=None, bus=None, route=None, status=None):
        return RouteRequest.objects.create(
            driver=driver or self.driver,
            bus=bus or self.bus,
            route=route or self.route,
            status=status or RouteRequest.STATUS_APPROVED,
        )

    def test_finish_completes_matching_approved_and_deactivates_bus(self):
        req = self._make_approved()
        route_id_before = self.bus.route_id
        res = self.client.post(f"/api/drivers/{self.driver.id}/finish-trip/")
        self.assertEqual(res.status_code, 200)
        req.refresh_from_db()
        self.bus.refresh_from_db()
        self.driver.refresh_from_db()
        self.assertEqual(req.status, RouteRequest.STATUS_COMPLETED)
        self.assertFalse(self.bus.is_active)
        # Finished trips clear Bus.route; driver assignment and historical request route are preserved.
        self.assertIsNone(self.bus.route_id)
        self.assertEqual(req.route_id, route_id_before)
        self.assertEqual(req.bus_id, self.bus.id)
        self.assertEqual(self.driver.assigned_bus_id, self.bus.id)
        self.assertTrue(res.json().get('completed'))
        self.assertEqual(res.json().get('completed_request_id'), req.id)

    def test_finish_with_no_bus_assigned_is_rejected(self):
        self.driver.assigned_bus = None
        self.driver.save(update_fields=['assigned_bus'])
        res = self.client.post(f"/api/drivers/{self.driver.id}/finish-trip/")
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

    def test_finish_is_idempotent_for_completed(self):
        req = self._make_approved(status=RouteRequest.STATUS_COMPLETED)
        res = self.client.post(f"/api/drivers/{self.driver.id}/finish-trip/")
        self.assertEqual(res.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, RouteRequest.STATUS_COMPLETED)
        self.assertFalse(res.json().get('completed'))

    def test_finish_ignores_pending_and_rejected(self):
        pending = self._make_approved(status=RouteRequest.STATUS_PENDING)
        rejected = self._make_approved(
            status=RouteRequest.STATUS_REJECTED,
            route=Route.objects.create(name='Other'),
        )
        res = self.client.post(f"/api/drivers/{self.driver.id}/finish-trip/")
        self.assertEqual(res.status_code, 200)
        pending.refresh_from_db()
        rejected.refresh_from_db()
        self.assertEqual(pending.status, RouteRequest.STATUS_PENDING)
        self.assertEqual(rejected.status, RouteRequest.STATUS_REJECTED)

    def test_finish_does_not_complete_other_bus_route_driver(self):
        other_route = Route.objects.create(name='Other Route')
        other_bus = Bus.objects.create(route=other_route, current_lat=0.1, current_lng=0.1)
        other_driver = Driver.objects.create(name='Other', assigned_bus=other_bus)
        foreign = self._make_approved(driver=other_driver, bus=other_bus, route=other_route)
        mine = self._make_approved()
        res = self.client.post(f"/api/drivers/{self.driver.id}/finish-trip/")
        self.assertEqual(res.status_code, 200)
        foreign.refresh_from_db()
        mine.refresh_from_db()
        self.assertEqual(foreign.status, RouteRequest.STATUS_APPROVED)
        self.assertEqual(mine.status, RouteRequest.STATUS_COMPLETED)

    def test_stop_trip_does_not_reset_stop_index(self):
        self.bus.current_stop_index = 5
        self.bus.save(update_fields=['current_stop_index'])
        self.client.post(f"/api/drivers/{self.driver.id}/stop-trip/")
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.current_stop_index, 5)
