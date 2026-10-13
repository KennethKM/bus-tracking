from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.test import SimpleTestCase, override_settings
from unittest.mock import patch

from .models import (
    Bus, Driver, DriverBusAssignment, Passenger, Route, Stop, StopTime, Trip,
    WaitingRequest,
)


class WaitingRequestEtaTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="passenger")
		self.passenger = Passenger.objects.create(
			user=self.user,
			name="Test Passenger",
		)
		self.other_user = User.objects.create_user(username="other-passenger")
		self.other_passenger = Passenger.objects.create(
			user=self.other_user,
			name="Other Passenger",
		)
		self.route = Route.objects.create(
			route_id="R1",
			route_long_name="Test Route",
		)
		self.trip = Trip.objects.create(
			trip_id="T1",
			route=self.route,
			trip_headsign="Destination",
			direction_id=0,
			shape_id="S1",
			service_id="SERVICE",
		)
		self.stops = [
			Stop.objects.create(
				stop_id=stop_id,
				stop_name=f"Stop {stop_id}",
				stop_lat=-15.4 + stop_id / 1000,
				stop_lon=28.3 + stop_id / 1000,
			)
			for stop_id in (1, 2, 3)
		]
		self.stop_times = [
			StopTime.objects.create(
				trip=self.trip,
				stop=stop,
				stop_sequence=sequence,
			)
			for sequence, stop in enumerate(self.stops, start=1)
		]
		self.waiting_request = WaitingRequest.objects.create(
			passenger=self.passenger,
			trip=self.trip,
			stop=self.stops[1],
			status="WAITING",
		)
		self.client.force_authenticate(user=self.user)

	def create_bus(self, registration_number="BUS1", **overrides):
		values = {
			"registration_number": registration_number,
			"is_active": True,
			"status": "IN_TRANSIT",
			"current_trip": self.trip,
			"current_stop_time": self.stop_times[0],
			"current_lat": -15.4,
			"current_lng": 28.3,
		}
		values.update(overrides)
		return Bus.objects.create(**values)

	def get_eta(self, waiting_request=None):
		request = waiting_request or self.waiting_request
		return self.client.get(
			f"/api/waiting-requests/{request.pk}/eta/"
		)

	@patch("tracking.services.eta_service.get_road_distance")
	def test_returns_smallest_osrm_duration_for_eligible_buses(self, get_road_distance):
		self.create_bus("BUS1")
		self.create_bus("BUS2", status="AT_STOP")
		get_road_distance.side_effect = [
			{"distance_meters": 1000, "duration_seconds": 720},
			{"distance_meters": 900, "duration_seconds": 300},
		]

		response = self.get_eta()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, {"eta_minutes": 5.0})
		self.assertEqual(get_road_distance.call_count, 2)

	@patch("tracking.services.eta_service.get_road_distance")
	def test_returns_unavailable_when_no_bus_has_gps(self, get_road_distance):
		self.create_bus("BUS1", current_lat=None, current_lng=None)

		response = self.get_eta()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, {"eta_minutes": None})
		get_road_distance.assert_not_called()

	@patch("tracking.services.eta_service.get_road_distance")
	def test_excludes_bus_that_has_passed_the_requested_stop(self, get_road_distance):
		self.create_bus("BUS1", current_stop_time=self.stop_times[2])

		response = self.get_eta()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, {"eta_minutes": None})
		get_road_distance.assert_not_called()

	@patch("tracking.services.eta_service.get_road_distance")
	def test_non_waiting_requests_have_no_eta(self, get_road_distance):
		self.create_bus("BUS1")
		for request_status in ("ON_BOARD", "COMPLETED", "CANCELLED", "EXPIRED"):
			with self.subTest(status=request_status):
				self.waiting_request.status = request_status
				self.waiting_request.save(update_fields=["status"])
				response = self.get_eta()
				self.assertEqual(response.status_code, 200)
				self.assertEqual(response.data, {"eta_minutes": None})
		get_road_distance.assert_not_called()

	@patch("tracking.services.eta_service.get_road_distance")
	def test_another_passenger_cannot_read_the_request_eta(self, get_road_distance):
		self.client.force_authenticate(user=self.other_user)

		response = self.get_eta()

		self.assertEqual(response.status_code, 404)
		get_road_distance.assert_not_called()

	@patch("tracking.services.eta_service.get_road_distance", side_effect=IndexError)
	def test_missing_osrm_route_returns_unavailable(self, get_road_distance):
		self.create_bus("BUS1")

		response = self.get_eta()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, {"eta_minutes": None})
		get_road_distance.assert_called_once()


class WaitingOverviewTests(APITestCase):
    def setUp(self):
        route = Route.objects.create(route_id="overview", route_long_name="Test Route")
        self.trip = Trip.objects.create(
            trip_id="overview-trip", route=route, trip_headsign="Bauleni",
            direction_id=0, shape_id="shape", service_id="service",
        )
        self.bauleni = Stop.objects.create(
            stop_id=443, stop_name="Bauleni station", stop_lat=-15.4, stop_lon=28.3,
        )
        self.godfrey = Stop.objects.create(
            stop_id=448, stop_name="Godfrey Chitalu Road", stop_lat=-15.5, stop_lon=28.4,
        )
        StopTime.objects.create(trip=self.trip, stop=self.godfrey, stop_sequence=1)
        target = StopTime.objects.create(
            trip=self.trip, stop=self.bauleni, stop_sequence=2,
        )
        self.bus = Bus.objects.create(
            registration_number="OVERVIEW", is_active=True, status="IN_TRANSIT",
            current_trip=self.trip, current_stop_time=target,
        )
        driver_user = User.objects.create_user(username="overview-driver")
        driver = Driver.objects.create(user=driver_user)
        DriverBusAssignment.objects.create(driver=driver, bus=self.bus)
        self.client.force_authenticate(user=driver_user)
        self.passenger = Passenger.objects.create(
            user=User.objects.create_user(username="overview-passenger"),
            name="Overview Passenger",
        )
        self.waiting_request = WaitingRequest.objects.create(
            passenger=self.passenger, trip=self.trip, stop=self.bauleni,
            status="WAITING",
        )
        self.url = "/api/buses/OVERVIEW/waiting-overview/"

    def test_counts_bauleni_boarding_request_only_at_bauleni(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["trip_id"], self.trip.pk)
        self.assertEqual(response.data["stops"], [
            {"stop_id": 448, "stop_name": "Godfrey Chitalu Road",
             "stop_sequence": 1, "waiting_count": 0},
            {"stop_id": 443, "stop_name": "Bauleni station",
             "stop_sequence": 2, "waiting_count": 1},
        ])

        # A separate passenger at Godfrey must not move or inflate Bauleni's count.
        other_passenger = Passenger.objects.create(
            user=User.objects.create_user(username="godfrey-passenger"),
            name="Godfrey Passenger",
        )
        WaitingRequest.objects.create(
            passenger=other_passenger, trip=self.trip, stop=self.godfrey,
            status="WAITING",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {stop["stop_name"]: stop["waiting_count"] for stop in response.data["stops"]},
            {"Godfrey Chitalu Road": 1, "Bauleni station": 1},
        )

    def test_excludes_non_waiting_requests_and_other_trips(self):
        self.waiting_request.status = "CANCELLED"
        self.waiting_request.save(update_fields=["status"])
        other_trip = Trip.objects.create(
            trip_id="other-trip", route=self.trip.route, trip_headsign="Bauleni",
            direction_id=0, shape_id="shape", service_id="service",
        )
        StopTime.objects.create(trip=other_trip, stop=self.bauleni, stop_sequence=1)
        WaitingRequest.objects.create(
            passenger=self.passenger, trip=other_trip, stop=self.bauleni,
            status="WAITING",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([stop["waiting_count"] for stop in response.data["stops"]], [0, 0])

    def test_no_active_trip_returns_no_stops(self):
        self.bus.current_trip = None
        self.bus.save(update_fields=["current_trip"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["trip_id"])
        self.assertEqual(response.data["stops"], [])


class ApiAccessSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="security-passenger")
        self.passenger = Passenger.objects.create(user=self.user, name="Private Name")
        self.driver_user = User.objects.create_user(username="security-driver")
        self.driver = Driver.objects.create(user=self.driver_user)
        self.route = Route.objects.create(route_id="SEC", route_long_name="Security Route")
        self.stop = Stop.objects.create(
            stop_id=900, stop_name="Destination", stop_lat=-15.4, stop_lon=28.3,
        )
        self.trip = Trip.objects.create(
            trip_id="SEC-08:00:00", route=self.route, trip_headsign="Destination",
            direction_id=0, shape_id="SEC", service_id="SEC",
        )
        StopTime.objects.create(trip=self.trip, stop=self.stop, stop_sequence=1)
        self.bus = Bus.objects.create(registration_number="SEC-BUS")
        self.assignment = DriverBusAssignment.objects.create(driver=self.driver, bus=self.bus)
        self.waiting = WaitingRequest.objects.create(
            passenger=self.passenger, trip=self.trip, stop=self.stop,
        )

    def test_generic_transport_writes_are_disabled(self):
        records = (("routes", self.route.pk), ("stops", self.stop.pk), ("buses", self.bus.pk))
        for user in (None, self.user, self.driver_user):
            self.client.force_authenticate(user=user)
            for resource, pk in records:
                for method, url in (
                    ("post", f"/api/{resource}/"),
                    ("put", f"/api/{resource}/{pk}/"),
                    ("patch", f"/api/{resource}/{pk}/"),
                    ("delete", f"/api/{resource}/{pk}/"),
                ):
                    with self.subTest(user=user, resource=resource, method=method):
                        response = getattr(self.client, method)(url, {}, format="json")
                        self.assertEqual(response.status_code, 405)
        self.assertTrue(Route.objects.filter(pk=self.route.pk).exists())
        self.assertTrue(Stop.objects.filter(pk=self.stop.pk).exists())
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.registration_number, "SEC-BUS")

    def test_passenger_directory_is_removed(self):
        for user in (None, self.user):
            self.client.force_authenticate(user=user)
            for url in ("/api/passengers/", f"/api/passengers/{self.passenger.pk}/"):
                with self.subTest(user=user, url=url):
                    self.assertEqual(self.client.get(url).status_code, 404)

    @patch("tracking.views.calculate_eta", return_value=5.0)
    def test_public_transport_reads_remain_available(self, calculate_eta):
        urls = (
            "/api/routes/", f"/api/routes/{self.route.pk}/",
            "/api/stops/", f"/api/stops/{self.stop.pk}/",
            "/api/buses/", f"/api/buses/{self.bus.pk}/",
            "/api/routes/search/?q=Security", "/api/routes/SEC/destinations/",
            "/api/routes/SEC/stops/?destination=Destination",
            f"/api/buses/{self.bus.pk}/eta/{self.stop.pk}/",
            f"/api/trips/{self.trip.pk}/stops/{self.stop.pk}/waiting-count/",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        calculate_eta.assert_called_once()

    def test_registration_and_login_endpoints_are_public(self):
        response = self.client.post("/api/auth/register/", {
            "username": "new-security-passenger", "password": "Testing-password-123",
            "name": "New Passenger", "email": "security@example.com",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        response = self.client.post("/api/auth/login/", {
            "username": "new-security-passenger", "password": "Testing-password-123",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.driver_user.set_password("Testing-password-123")
        self.driver_user.save()
        response = self.client.post("/api/auth/driver/login/", {
            "username": self.driver_user.username, "password": "Testing-password-123",
        }, format="json")
        self.assertEqual(response.status_code, 200)

    def test_assigned_driver_can_update_gps(self):
        self.client.force_authenticate(user=self.driver_user)
        response = self.client.post("/api/buses/SEC-BUS/location/", {
            "lat": -15.4, "lng": 28.3, "speed": 10,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.bus.refresh_from_db()
        self.assertEqual((self.bus.current_lat, self.bus.current_lng, self.bus.speed), (-15.4, 28.3, 10))

    def test_assigned_driver_can_operate_bus(self):
        self.client.force_authenticate(user=self.driver_user)
        for operation in ("activate", "start-fresh", "deactivate"):
            with self.subTest(operation=operation):
                self.assertEqual(self.client.post(f"/api/buses/SEC-BUS/{operation}/").status_code, 200)
        response = self.client.post("/api/buses/start-trip/", {
            "registration_number": "SEC-BUS", "route_id": "SEC", "destination": "Destination",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.current_trip, self.trip)

    def test_driver_operations_require_active_driver_and_assignment(self):
        unassigned = User.objects.create_user(username="unassigned-security-driver")
        Driver.objects.create(user=unassigned)
        for user, active_driver, active_assignment in (
            (None, True, True), (self.user, True, True), (unassigned, True, True),
            (self.driver_user, False, True), (self.driver_user, True, False),
        ):
            self.driver.is_active = active_driver
            self.driver.save()
            self.assignment.is_active = active_assignment
            self.assignment.save()
            self.client.force_authenticate(user=user)
            for operation in ("activate", "deactivate", "start-fresh", "location"):
                with self.subTest(user=user, operation=operation, active_driver=active_driver, active_assignment=active_assignment):
                    self.assertEqual(self.client.post(f"/api/buses/SEC-BUS/{operation}/", {
                        "lat": -15.4, "lng": 28.3,
                    }, format="json").status_code, 403)
            self.assertEqual(self.client.post("/api/buses/start-trip/", {
                "registration_number": "SEC-BUS", "route_id": "SEC", "destination": "Destination",
            }, format="json").status_code, 403)
            self.assertEqual(self.client.get("/api/buses/SEC-BUS/waiting-overview/").status_code, 403)
        self.bus.refresh_from_db()
        self.assertIsNone(self.bus.current_lat)
        self.assertIsNone(self.bus.current_trip)
        self.assertFalse(self.bus.is_active)

    def test_expiry_requires_administrator(self):
        other = User.objects.create_user(username="other-security-passenger")
        Passenger.objects.create(user=other, name="Other Passenger")
        for user in (None, other, self.user, self.driver_user):
            self.client.force_authenticate(user=user)
            with self.subTest(user=user):
                response = self.client.post(f"/api/waiting-requests/{self.waiting.pk}/expire/")
                self.assertEqual(response.status_code, 403)
                self.waiting.refresh_from_db()
                self.assertEqual(self.waiting.status, "WAITING")
                self.assertIsNone(self.waiting.deactivated_at)
        admin = User.objects.create_user(username="security-admin", is_staff=True)
        self.client.force_authenticate(user=admin)
        self.assertEqual(self.client.post(f"/api/waiting-requests/{self.waiting.pk}/expire/").status_code, 200)
        self.waiting.refresh_from_db()
        self.assertEqual(self.waiting.status, "EXPIRED")
        self.assertIsNotNone(self.waiting.deactivated_at)

    def test_default_permission_requires_authentication(self):
        from rest_framework.permissions import IsAuthenticated
        from rest_framework.settings import api_settings
        self.assertEqual(api_settings.DEFAULT_PERMISSION_CLASSES, [IsAuthenticated])
        for url in ("/api/auth/me/", "/api/auth/driver/me/", "/api/waiting-requests/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)


    def test_registration_rejects_invalid_passwords_without_creating_accounts(self):
        for password in ("short", "password", "123456789012", "validator-person"):
            with self.subTest(password=password):
                response = self.client.post("/api/auth/register/", {
                    "username": "validator-person", "email": "validator@example.com",
                    "name": "Validator Person", "password": password,
                }, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.data["error"], str)
                self.assertTrue(response.data["password"])
                self.assertFalse(User.objects.filter(username="validator-person").exists())
                self.assertEqual(Passenger.objects.count(), 1)

    def test_registration_uses_configured_password_validators(self):
        from django.test import override_settings
        with override_settings(AUTH_PASSWORD_VALIDATORS=[{
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 40},
        }]):
            response = self.client.post("/api/auth/register/", {
                "username": "configured-validator", "email": "configured@example.com",
                "name": "Configured Validator", "password": "Testing-password-123",
            }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("40", response.data["error"])
        self.assertFalse(User.objects.filter(username="configured-validator").exists())

    def test_owner_cannot_update_or_delete_waiting_request_directly(self):
        self.client.force_authenticate(user=self.user)
        original_created_at = self.waiting.created_at
        url = f"/api/waiting-requests/{self.waiting.pk}/"
        for method in ("put", "patch", "delete"):
            for requested_status in ("ON_BOARD", "COMPLETED", "EXPIRED"):
                with self.subTest(method=method, status=requested_status):
                    response = getattr(self.client, method)(url, {
                        "trip": self.trip.pk, "stop": self.stop.pk,
                        "status": requested_status,
                        "created_at": "2000-01-01T00:00:00Z",
                        "deactivated_at": "2000-01-01T00:00:00Z",
                    }, format="json")
                    self.assertEqual(response.status_code, 405)
                    self.waiting.refresh_from_db()
                    self.assertEqual(self.waiting.status, "WAITING")
                    self.assertEqual(self.waiting.created_at, original_created_at)
                    self.assertIsNone(self.waiting.deactivated_at)

    def test_creation_ignores_client_supplied_lifecycle_fields(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.post(
            f"/api/waiting-requests/{self.waiting.pk}/cancel/",
        ).status_code, 200)
        for requested_status in ("ON_BOARD", "COMPLETED", "EXPIRED"):
            with self.subTest(status=requested_status):
                response = self.client.post("/api/waiting-requests/", {
                    "trip": self.trip.pk, "stop": self.stop.pk,
                    "status": requested_status, "passenger": 99999,
                    "created_at": "2000-01-01T00:00:00Z",
                    "deactivated_at": "2000-01-01T00:00:00Z",
                }, format="json")
                self.assertEqual(response.status_code, 201)
                created = WaitingRequest.objects.get(pk=response.data["id"])
                self.assertEqual(created.status, "WAITING")
                self.assertEqual(created.passenger, self.passenger)
                self.assertIsNone(created.deactivated_at)
                self.assertGreater(created.created_at.year, 2000)
                self.assertEqual(self.client.post(
                    f"/api/waiting-requests/{created.pk}/cancel/",
                ).status_code, 200)
                created.refresh_from_db()
                self.assertEqual(created.status, "CANCELLED")
                self.assertIsNotNone(created.deactivated_at)

    def test_owner_can_board_and_complete_through_workflow_actions(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get("/api/waiting-requests/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/waiting-requests/{self.waiting.pk}/").status_code, 200)
        self.assertEqual(self.client.post(
            f"/api/waiting-requests/{self.waiting.pk}/board/",
        ).status_code, 200)
        self.waiting.refresh_from_db()
        self.assertEqual(self.waiting.status, "ON_BOARD")
        self.assertEqual(self.client.post(
            f"/api/waiting-requests/{self.waiting.pk}/complete/",
        ).status_code, 200)
        self.waiting.refresh_from_db()
        self.assertEqual(self.waiting.status, "COMPLETED")
        self.assertIsNotNone(self.waiting.deactivated_at)

    def test_other_passenger_cannot_use_workflow_actions(self):
        other_user = User.objects.create_user(username="workflow-other")
        Passenger.objects.create(user=other_user, name="Other Passenger")
        self.client.force_authenticate(user=other_user)
        for action, current_status in (("cancel", "WAITING"), ("board", "WAITING"), ("complete", "ON_BOARD")):
            self.waiting.status = current_status
            self.waiting.save(update_fields=["status"])
            response = self.client.post(f"/api/waiting-requests/{self.waiting.pk}/{action}/")
            self.assertEqual(response.status_code, 404)
            self.waiting.refresh_from_db()
            self.assertEqual(self.waiting.status, current_status)


    def test_anonymous_waiting_request_paths_return_forbidden(self):
        self.assert_waiting_request_paths_forbidden(None)

    def test_non_passenger_waiting_request_paths_return_forbidden(self):
        self.assert_waiting_request_paths_forbidden(self.driver_user)
        user = User.objects.create_user(username="no-passenger-profile")
        self.assert_waiting_request_paths_forbidden(user)

    def assert_waiting_request_paths_forbidden(self, user):
        self.client.force_authenticate(user=user)
        detail = f"/api/waiting-requests/{self.waiting.pk}/"
        paths = [("get", "/api/waiting-requests/"), ("get", detail),
                 ("post", "/api/waiting-requests/")]
        paths += [("post", detail + action + "/") for action in ("board", "cancel", "complete")]
        paths += [("get", detail + "eta/")]
        for method, url in paths:
            with self.subTest(user=user, method=method, url=url):
                response = getattr(self.client, method)(url, {
                    "trip": self.trip.pk, "stop": self.stop.pk,
                }, format="json")
                self.assertEqual(response.status_code, 403)
                self.waiting.refresh_from_db()
                self.assertEqual(self.waiting.status, "WAITING")
                self.assertEqual(WaitingRequest.objects.count(), 1)

    def test_waiting_request_reads_remain_owner_scoped(self):
        other = User.objects.create_user(username="request-read-other")
        Passenger.objects.create(user=other, name="Other Passenger")
        self.client.force_authenticate(user=other)
        response = self.client.get("/api/waiting-requests/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.assertEqual(self.client.get(
            f"/api/waiting-requests/{self.waiting.pk}/",
        ).status_code, 404)


    def test_viewset_profile_guards_also_protect_direct_method_calls(self):
        from types import SimpleNamespace
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.exceptions import PermissionDenied
        from .views import WaitingRequestViewSet
        for user in (AnonymousUser(), self.driver_user):
            view = WaitingRequestViewSet()
            view.request = SimpleNamespace(user=user)
            with self.subTest(user=user):
                with self.assertRaises(PermissionDenied):
                    view.get_queryset()
                with self.assertRaises(PermissionDenied):
                    view.perform_create(None)

    def test_non_passenger_creation_is_forbidden_before_payload_validation(self):
        self.client.force_authenticate(user=self.driver_user)
        self.assertEqual(self.client.post("/api/waiting-requests/", {}, format="json").status_code, 403)


@override_settings(CACHES={"default": {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "login-throttle-tests",
}})
class LoginThrottleTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.addCleanup(cache.clear)

    def assert_login_limit(self, url):
        from rest_framework.throttling import SimpleRateThrottle
        with patch.object(SimpleRateThrottle, "timer", return_value=1000):
            for attempt in range(5):
                response = self.client.post(url, {
                    "username": f"missing-{attempt}", "password": "wrong-password",
                }, format="json", REMOTE_ADDR="192.0.2.1")
                self.assertEqual(response.status_code, 401)
            response = self.client.post(url, {}, format="json", REMOTE_ADDR="192.0.2.1")
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.data["detail"].code, "throttled")
            self.assertEqual(response["Retry-After"], "60")
            self.assertEqual(self.client.post(
                url, {}, format="json", REMOTE_ADDR="192.0.2.2",
            ).status_code, 400)
        with patch.object(SimpleRateThrottle, "timer", return_value=1060):
            self.assertEqual(self.client.post(
                url, {}, format="json", REMOTE_ADDR="192.0.2.1",
            ).status_code, 400)

    def test_passenger_login_rate_limit(self):
        self.assert_login_limit("/api/auth/login/")

    def test_driver_login_rate_limit(self):
        self.assert_login_limit("/api/auth/driver/login/")

    def test_login_limits_are_separate_and_registration_is_unthrottled(self):
        for url in ("/api/auth/login/", "/api/auth/driver/login/"):
            for attempt in range(5):
                self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
            self.assertEqual(self.client.post(url, {}, format="json").status_code, 429)
        for attempt in range(6):
            self.assertEqual(self.client.post("/api/auth/register/", {}, format="json").status_code, 400)
        self.assertEqual(self.client.get("/api/routes/search/").status_code, 200)

    def test_authenticated_requests_are_also_limited_by_ip(self):
        for url in ("/api/auth/login/", "/api/auth/driver/login/"):
            for attempt in range(5):
                user = User.objects.create_user(username=f"{url}-{attempt}")
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
            self.assertEqual(self.client.post(url, {}, format="json").status_code, 429)


class DebugDefaultTests(SimpleTestCase):
    def load_settings(self, debug=None):
        import os
        import runpy
        from pathlib import Path
        environment = {"DJANGO_SECRET_KEY": "test-only-settings-secret"}
        if debug is not None:
            environment["DJANGO_DEBUG"] = debug
        with patch.dict(os.environ, environment, clear=True):
            return runpy.run_path(str(Path(__file__).resolve().parents[1] / "bus_tracking" / "settings.py"))

    def test_debug_is_false_when_environment_variable_is_absent(self):
        self.assertIs(self.load_settings()["DEBUG"], False)

    def test_debug_can_be_explicitly_enabled_for_local_development(self):
        self.assertIs(self.load_settings("True")["DEBUG"], True)
