from django.test import SimpleTestCase

from tracking.frontend_compat import (
    normalize_route_search,
    normalize_route_destinations,
    normalize_trip_stops,
)


class FrontendCompatibilityTests(SimpleTestCase):
    def test_route_search_normalizes_integration_payload(self):
        payload = [
            {"route_id": "L1", "route_long_name": "CBD to Kanyama"},
            {"route_id": "L2", "route_long_name": "Chelston to Town"},
        ]

        normalized = normalize_route_search(payload)

        self.assertEqual(normalized[0]["id"], "L1")
        self.assertEqual(normalized[0]["label"], "CBD to Kanyama")
        self.assertEqual(normalized[1]["id"], "L2")

    def test_route_destinations_extracts_destination_values(self):
        payload = [{"destination": "Town"}, {"destination": "Kanyama"}]

        self.assertEqual(normalize_route_destinations(payload), ["Town", "Kanyama"])

    def test_trip_stops_return_ui_shapes(self):
        payload = {
            "trip_id": "L1-08:00:00",
            "destination": "Town",
            "stops": [
                {"stop_id": 101, "stop_name": "Central Market", "stop_sequence": 1},
                {"stop_id": 102, "stop_name": "Town", "stop_sequence": 2},
            ],
        }

        normalized = normalize_trip_stops(payload)

        self.assertEqual(normalized["tripId"], "L1-08:00:00")
        self.assertEqual(normalized["stops"][0]["name"], "Central Market")
        self.assertEqual(normalized["stops"][1]["id"], 102)
