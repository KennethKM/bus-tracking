from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from .models import Bus, Driver, Route, Stop, Passenger, RouteRequest


class DriverInterfaceActiveRouteTests(TestCase):
    def _make_route_with_bus_driver(self, route_name='Central Loop'):
        route = Route.objects.create(name=route_name)
        bus = Bus.objects.create(route=route, current_lat=1.0, current_lng=2.0, speed=10)
        driver = Driver.objects.create(name='Mina', assigned_bus=bus)
        return route, bus, driver

    def test_approved_request_displays_route(self):
        route, bus, driver = self._make_route_with_bus_driver()
        RouteRequest.objects.create(driver=driver, bus=bus, route=route, status=RouteRequest.STATUS_APPROVED)
        response = self.client.get(reverse('driver_interface', args=[driver.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['approved_route'], route)
        self.assertEqual(response.context['route'], route)
        self.assertTrue(response.context['has_active_route'])
        self.assertContains(response, route.name)

    def test_completed_request_shows_default_empty_state(self):
        route, bus, driver = self._make_route_with_bus_driver()
        RouteRequest.objects.create(driver=driver, bus=bus, route=route, status=RouteRequest.STATUS_COMPLETED)
        response = self.client.get(reverse('driver_interface', args=[driver.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['approved_route'])
        self.assertIsNone(response.context['route'])
        self.assertFalse(response.context['has_active_route'])
        self.assertContains(response, 'No assigned route yet')
        self.assertContains(response, 'No approved route.')
        self.assertContains(response, 'No route selected')
        # Assigned bus must remain visible even without an active route.
        self.assertContains(response, f'Assigned Bus #{bus.id}')

    def test_no_bus_shows_unavailable_trip_controls_and_keeps_map(self):
        driver = Driver.objects.create(name='Solo')
        response = self.client.get(reverse('driver_interface', args=[driver.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="noAssignedBus"')
        self.assertContains(response, 'No bus assigned. Trip controls unavailable.')
        self.assertNotContains(response, 'id="startTripBtn"')
        self.assertNotContains(response, 'id="stopTripBtn"')
        # Driver GPS/map functionality must remain available.
        self.assertContains(response, 'Your live location')
        self.assertContains(response, 'id="lat"')


class DriverAdminAssignTests(TestCase):
    def test_unassign_action_clears_assigned_bus(self):
        from django.contrib.admin.sites import AdminSite
        from .admin import DriverAdmin
        bus = Bus.objects.create(current_lat=1.0, current_lng=2.0)
        driver = Driver.objects.create(name='Mina', assigned_bus=bus)
        site = AdminSite()
        admin = DriverAdmin(Driver, site)
        admin.unassign_bus(request=None, queryset=Driver.objects.filter(id=driver.id))
        driver.refresh_from_db()
        self.assertIsNone(driver.assigned_bus)

    def test_direct_assigned_bus_edit_still_works(self):
        bus = Bus.objects.create(current_lat=1.0, current_lng=2.0)
        driver = Driver.objects.create(name='Mina')
        driver.assigned_bus = bus
        driver.save(update_fields=['assigned_bus'])
        driver.refresh_from_db()
        self.assertEqual(driver.assigned_bus_id, bus.id)

    def test_route_request_admin_bus_column_shows_stable_bus_identity(self):
        route_a = Route.objects.create(name='Route A')
        route_b = Route.objects.create(name='Route B')
        bus = Bus.objects.create(route=route_a, current_lat=1.0, current_lng=2.0)
        RouteRequest.objects.create(
            driver=Driver.objects.create(name='Test Driver'),
            bus=bus,
            route=route_b,
            status=RouteRequest.STATUS_APPROVED,
        )
        bus.route = route_a
        bus.save(update_fields=['route'])

        from django.contrib.admin.sites import AdminSite
        from .admin import RouteRequestAdmin
        site = AdminSite()
        admin = RouteRequestAdmin(RouteRequest, site)

        request = RouteRequest.objects.first()
        bus_display = admin.bus_short(request)

        self.assertEqual(bus_display, 'Bus 1')
        self.assertEqual(request.route, route_b)

    def test_driver_admin_assigned_bus_shows_approved_route(self):
        route = Route.objects.create(name='Route B')
        bus = Bus.objects.create(route=route, current_lat=1.0, current_lng=2.0)
        driver = Driver.objects.create(name='Test Driver', assigned_bus=bus)
        RouteRequest.objects.create(
            driver=driver,
            bus=bus,
            route=route,
            status=RouteRequest.STATUS_APPROVED,
        )

        from django.contrib.admin.sites import AdminSite
        from .admin import DriverAdmin
        site = AdminSite()
        admin = DriverAdmin(Driver, site)

        driver_from_db = Driver.objects.get(id=driver.id)
        self.assertEqual(admin.assigned_bus_display(driver_from_db), 'Bus 1 to Route B')

    def test_driver_admin_assigned_bus_falls_back_without_approved_request(self):
        route = Route.objects.create(name='Route A')
        bus = Bus.objects.create(route=route, current_lat=1.0, current_lng=2.0)
        driver = Driver.objects.create(name='Test Driver', assigned_bus=bus)

        from django.contrib.admin.sites import AdminSite
        from .admin import DriverAdmin
        site = AdminSite()
        admin = DriverAdmin(Driver, site)

        driver_from_db = Driver.objects.get(id=driver.id)
        self.assertEqual(admin.assigned_bus_display(driver_from_db), 'Bus 1')

class BusRouteLifecycleTests(TestCase):
    """Tests for Bus.route lifecycle after approval and completion."""

    def setUp(self):
        self.client = Client()
        self.route_a = Route.objects.create(name='Route A: Chelstone - Town (Millenium)')
        self.route_b = Route.objects.create(name='Route B: Chelstone - Kulima Tower')
        self.bus = Bus.objects.create(
            route=self.route_a,
            registration_number='ABC123',
            capacity=40,
            current_lat=0.0,
            current_lng=0.0,
            current_stop_index=0,
            speed=0,
            is_active=False,
        )
        self.driver = Driver.objects.create(
            name='Driver 1',
            license_number='A12345',
            assigned_bus=self.bus,
            is_active=True,
        )

    def test_approval_updates_bus_route(self):
        """Pending request for Bus + Route B → after approval, Bus.route == Route B."""
        pending_request = RouteRequest.objects.create(
            driver=self.driver,
            bus=self.bus,
            route=self.route_b,
            status=RouteRequest.STATUS_PENDING,
        )
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.route, self.route_a)

        response = self.client.post(
            reverse('approve_route_request', args=[pending_request.id]),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        pending_request.refresh_from_db()
        self.bus.refresh_from_db()
        self.assertEqual(pending_request.status, RouteRequest.STATUS_APPROVED)
        self.assertEqual(pending_request.route, self.route_b)
        self.assertEqual(self.bus.route, self.route_b)
        self.assertEqual(self.driver.assigned_bus, self.bus)



class WebsiteViewTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bus Tracking')
        self.assertContains(response, 'Driver Portal')
        self.assertContains(response, 'Passenger Portal')

    def test_home_page_has_three_access_options(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, '/drivers/1/interface/')
        self.assertContains(response, '/admin/')
        self.assertContains(response, '/passenger/portal/')


class PassengerPortalTests(TestCase):
    def test_passenger_signup_creates_passenger_and_redirects(self):
        response = self.client.post(reverse('passenger_portal'), {"action": "signup", "name": "Alice"})
        # Should redirect to profile
        self.assertEqual(response.status_code, 302)
        passenger = Passenger.objects.filter(name="Alice").first()
        self.assertIsNotNone(passenger)


class DriverInterfaceViewTests(TestCase):
    def test_driver_interface_exposes_publish_endpoint_for_geolocation(self):
        route = Route.objects.create(name='Central Loop')
        bus = Bus.objects.create(route=route, current_lat=1.0, current_lng=2.0, speed=10)
        driver = Driver.objects.create(name='Mina', assigned_bus=bus)

        response = self.client.get(reverse('driver_interface', args=[driver.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/drivers/{}/location/'.format(driver.id))

    def test_driver_interface_displays_assigned_bus_and_route(self):
        route = Route.objects.create(name='Central Loop')
        Stop.objects.create(route=route, name='Central', latitude=1.0, longitude=2.0, order=1)
        Stop.objects.create(route=route, name='Airport', latitude=3.0, longitude=4.0, order=2)
        bus = Bus.objects.create(
            route=route,
            current_lat=1.234,
            current_lng=2.345,
            speed=18,
        )
        driver = Driver.objects.create(name='Mina', assigned_bus=bus)

        response = self.client.get(reverse('driver_interface', args=[driver.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Driver Dashboard')
        self.assertContains(response, driver.name)
        self.assertContains(response, route.name)
        self.assertContains(response, 'Central')

    def test_driver_interface_creates_demo_driver_when_id_is_missing(self):
        response = self.client.get(reverse('driver_interface', args=[999]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Driver Dashboard')
        self.assertContains(response, 'Driver 999')

    def test_driver_interface_shows_live_location_ui_without_assigned_bus(self):
        response = self.client.get(reverse('driver_interface', args=[999]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your live location')
        self.assertContains(response, 'Live location shown on map')

    def test_driver_interface_map_assets_are_not_blocked_by_invalid_integrity(self):
        route = Route.objects.create(name='Central Loop')
        bus = Bus.objects.create(route=route, current_lat=1.0, current_lng=2.0, speed=10)
        driver = Driver.objects.create(name='Mina', assigned_bus=bus)

        response = self.client.get(reverse('driver_interface', args=[driver.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'leaflet.js')
        self.assertNotContains(response, 'integrity="sha256-o9N1j8k0ZbNfKkGk3bKkP0sKpGk2b1V9+8qv+0hXQnM=' )
