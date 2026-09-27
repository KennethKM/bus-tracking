import os
import tempfile
import zipfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Route, Stop, Bus, Driver, RouteRequest


class RouteRequestTests(TestCase):
    def setUp(self):
        self.route = Route.objects.create(name='Kanyama - Town', origin='Kanyama', destination='Town')
        self.other_route = Route.objects.create(name='Mandevu - CBD', origin='Mandevu', destination='CBD')
        self.bus = Bus.objects.create(
            route=self.route,
            registration_number='BUS001',
            capacity=40,
            current_lat=-15.388,
            current_lng=28.322,
            current_stop_index=0,
            speed=0,
            is_active=False,
        )
        self.driver = Driver.objects.create(
            name='Driver 1',
            license_number='DEMO-LICENSE-001',
            assigned_bus=self.bus,
            is_active=True,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
        )

    def test_route_request_defaults_to_pending(self):
        request = RouteRequest.objects.create(
            driver=self.driver,
            route=self.route,
            bus=self.bus,
        )
        self.assertEqual(request.status, RouteRequest.STATUS_PENDING)

    def test_driver_can_request_existing_route(self):
        response = self.client.post(
            reverse('request_route_for_driver', args=[self.driver.id]),
            {'route_id': self.route.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['status'], RouteRequest.STATUS_PENDING)
        self.assertEqual(body['route_id'], self.route.id)

    def test_invalid_driver_returns_error(self):
        response = self.client.post(
            reverse('request_route_for_driver', args=[9999]),
            {'route_id': self.route.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_driver_without_bus_cannot_request_route(self):
        driver = Driver.objects.create(name='Driver 2', license_number='X', is_active=True)
        response = self.client.post(
            reverse('request_route_for_driver', args=[driver.id]),
            {'route_id': self.route.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_route_returns_error(self):
        response = self.client.post(
            reverse('request_route_for_driver', args=[self.driver.id]),
            {'route_id': 9999},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_pending_request_is_prevented(self):
        RouteRequest.objects.create(
            driver=self.driver,
            route=self.route,
            bus=self.bus,
            status=RouteRequest.STATUS_PENDING,
        )
        response = self.client.post(
            reverse('request_route_for_driver', args=[self.driver.id]),
            {'route_id': self.route.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 409)

    def test_admin_can_approve_pending_request(self):
        route_request = RouteRequest.objects.create(
            driver=self.driver,
            route=self.other_route,
            bus=self.bus,
            status=RouteRequest.STATUS_PENDING,
        )
        response = self.client.post(
            reverse('approve_route_request', args=[route_request.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        route_request.refresh_from_db()
        self.assertEqual(route_request.status, RouteRequest.STATUS_APPROVED)
        self.assertIsNotNone(route_request.approved_at)
        bus_from_db = Bus.objects.get(id=self.bus.id)
        self.assertEqual(bus_from_db.route_id, self.other_route.id)

    def test_admin_can_reject_pending_request(self):
        route_request = RouteRequest.objects.create(
            driver=self.driver,
            route=self.other_route,
            bus=self.bus,
            status=RouteRequest.STATUS_PENDING,
        )
        response = self.client.post(
            reverse('reject_route_request', args=[route_request.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        route_request.refresh_from_db()
        self.assertEqual(route_request.status, RouteRequest.STATUS_REJECTED)
        self.assertIsNone(route_request.approved_at)

    def test_driver_can_see_approved_route(self):
        route_request = RouteRequest.objects.create(
            driver=self.driver,
            route=self.other_route,
            bus=self.bus,
            status=RouteRequest.STATUS_APPROVED,
            approved_at='2024-01-01T00:00:00Z'
        )
        response = self.client.get(reverse('driver_interface', args=[self.driver.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved Route')
        self.assertContains(response, self.other_route.name)

    def test_registered_driver_list_contains_demo_driver(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/admin/tracking/driver/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Driver 1')
        self.assertContains(response, 'DEMO-LICENSE-001')
        # Without an APPROVED RouteRequest, the assigned bus displays as stable identity.
        self.assertContains(response, 'Bus 1')

    def test_demo_seed_command_creates_driver_one_and_bus_one(self):
        call_command('seed_demo_driver')

        driver = Driver.objects.filter(name='Driver 1').first()
        self.assertIsNotNone(driver)
        self.assertEqual(driver.license_number, 'A12345')
        self.assertTrue(driver.is_active)

        bus = Bus.objects.filter(registration_number='ABC123').first()
        self.assertIsNotNone(bus)
        self.assertEqual(bus.route_id, None)
        self.assertFalse(bus.is_active)
        self.assertEqual(driver.assigned_bus_id, bus.id)

    def test_seed_gtfs_routes_imports_routes_and_stops_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, 'gtfs.zip')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(
                    'routes.txt',
                    'route_id,route_short_name,route_long_name,route_type\nR1,Kasupe,Kasupe - Town,3\n'
                )
                zf.writestr(
                    'stops.txt',
                    'stop_id,stop_name,stop_lat,stop_lon\nS1,Central,-15.40,28.30\nS2,Town,-15.50,28.40\n'
                )
                zf.writestr(
                    'trips.txt',
                    'route_id,trip_id,service_id\nR1,T1,WD\n'
                )
                zf.writestr(
                    'stop_times.txt',
                    'trip_id,arrival_time,departure_time,stop_id,stop_sequence\nT1,08:00:00,08:00:00,S1,1\nT1,08:10:00,08:10:00,S2,2\n'
                )

            with patch('tracking.management.commands.seed_gtfs_routes.get_gtfs_zip_path', return_value=zip_path):
                call_command('seed_gtfs_routes')
                call_command('seed_gtfs_routes')

        routes = Route.objects.filter(name__icontains='Kasupe')
        self.assertEqual(routes.count(), 1)
        stops = Stop.objects.filter(route__name__icontains='Kasupe').order_by('order')
        self.assertEqual(stops.count(), 2)
        self.assertEqual([s.name for s in stops], ['Central', 'Town'])
