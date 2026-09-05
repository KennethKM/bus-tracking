from django.test import TestCase
from django.urls import reverse

from .models import Bus, Driver, Route, Stop, Passenger


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
