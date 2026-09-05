from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .serializers import LocationSerializer
from .services.location_service import save_bus_location
from .models import Route, Bus, Driver
import math


class LocationSerializerTests(TestCase):
    def test_valid_payload_is_accepted(self):
        s = LocationSerializer(data={"lat": 10.0, "lng": 20.0, "speed": 30.0})
        self.assertTrue(s.is_valid(), s.errors)

    def test_latitude_below_minus_90_is_rejected(self):
        s = LocationSerializer(data={"lat": -91.0, "lng": 0.0, "speed": 0})
        self.assertFalse(s.is_valid())
        self.assertIn('lat', s.errors)

    def test_latitude_above_90_is_rejected(self):
        s = LocationSerializer(data={"lat": 91.0, "lng": 0.0, "speed": 0})
        self.assertFalse(s.is_valid())
        self.assertIn('lat', s.errors)

    def test_longitude_below_minus_180_is_rejected(self):
        s = LocationSerializer(data={"lat": 0.0, "lng": -181.0, "speed": 0})
        self.assertFalse(s.is_valid())
        self.assertIn('lng', s.errors)

    def test_longitude_above_180_is_rejected(self):
        s = LocationSerializer(data={"lat": 0.0, "lng": 181.0, "speed": 0})
        self.assertFalse(s.is_valid())
        self.assertIn('lng', s.errors)

    def test_negative_speed_is_rejected(self):
        s = LocationSerializer(data={"lat": 0.0, "lng": 0.0, "speed": -1})
        self.assertFalse(s.is_valid())
        self.assertIn('speed', s.errors)

    def test_non_numeric_coordinates_are_rejected(self):
        s = LocationSerializer(data={"lat": "x", "lng": "y"})
        self.assertFalse(s.is_valid())

    def test_missing_speed_uses_default(self):
        s = LocationSerializer(data={"lat": 1.0, "lng": 2.0})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data.get('speed', None), 0.0)


class LocationServiceTests(TestCase):
    def setUp(self):
        self.route = Route.objects.create(name='Test Route')
        self.bus = Bus.objects.create(route=self.route, current_lat=1.0, current_lng=1.0, speed=10)

    def test_save_bus_location_updates_bus(self):
        bus = save_bus_location(self.bus.id, 10.0, 20.0, 15.0)
        self.assertEqual(bus.current_lat, 10.0)
        self.assertEqual(bus.current_lng, 20.0)
        self.assertEqual(bus.speed, 15.0)

    def test_invalid_latitude_raises(self):
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, -200.0, 0.0, 10.0)

    def test_invalid_longitude_raises(self):
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, 0.0, 200.0, 10.0)

    def test_negative_speed_raises(self):
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, 10.0, 20.0, -5.0)

    def test_nan_and_infinite_are_rejected(self):
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, math.nan, 0.0, 10.0)
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, 0.0, math.inf, 10.0)

    def test_zero_zero_rejected(self):
        with self.assertRaises(ValueError):
            save_bus_location(self.bus.id, 0.0, 0.0, 0.0)

    def test_speed_above_cap_is_capped(self):
        bus = save_bus_location(self.bus.id, 10.0, 20.0, 500.0)
        # implementation caps at 200.0
        self.assertEqual(bus.speed, 200.0)


class DriverLocationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.route = Route.objects.create(name='D Route')
        self.bus = Bus.objects.create(route=self.route, current_lat=1.0, current_lng=1.0, speed=5)
        self.driver = Driver.objects.create(name='Drv', assigned_bus=self.bus)

    def test_valid_driver_location_update_returns_200(self):
        url = reverse('update_driver_location', args=[self.driver.id])
        res = self.client.post(url, {"lat": 11.0, "lng": 12.0, "speed": 20.0}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_invalid_coordinates_return_400(self):
        url = reverse('update_driver_location', args=[self.driver.id])
        res = self.client.post(url, {"lat": 999, "lng": 12.0, "speed": 20.0}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_invalid_speed_returns_400(self):
        url = reverse('update_driver_location', args=[self.driver.id])
        res = self.client.post(url, {"lat": 11.0, "lng": 12.0, "speed": -5.0}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_unassigned_driver_returns_error(self):
        drv = Driver.objects.create(name='NoBus', assigned_bus=None)
        url = reverse('update_driver_location', args=[drv.id])
        res = self.client.post(url, {"lat": 11.0, "lng": 12.0, "speed": 10.0}, format='json')
        # existing behavior returns 400 with error about no assigned bus
        self.assertEqual(res.status_code, 400)

    def test_nonexistent_driver_returns_404(self):
        url = reverse('update_driver_location', args=[99999])
        res = self.client.post(url, {"lat": 11.0, "lng": 12.0, "speed": 10.0}, format='json')
        self.assertEqual(res.status_code, 404)


class BusLocationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.route = Route.objects.create(name='B Route')
        self.bus = Bus.objects.create(route=self.route, current_lat=0.5, current_lng=0.5, speed=5)

    def test_valid_bus_location_update_returns_200(self):
        url = f'/buses/{self.bus.id}/location/'
        res = self.client.post(url, {"lat": 10.0, "lng": 11.0, "speed": 20.0}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_invalid_bus_coordinates_return_400(self):
        url = f'/buses/{self.bus.id}/location/'
        res = self.client.post(url, {"lat": -200.0, "lng": 11.0, "speed": 20.0}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_invalid_bus_speed_return_400(self):
        url = f'/buses/{self.bus.id}/location/'
        res = self.client.post(url, {"lat": 10.0, "lng": 11.0, "speed": -10.0}, format='json')
        self.assertEqual(res.status_code, 400)
