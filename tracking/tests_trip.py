from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Driver, Bus


class TripEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from .models import Route
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
