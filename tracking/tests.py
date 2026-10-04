from django.contrib.auth.models import User
from rest_framework.test import APITestCase
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
