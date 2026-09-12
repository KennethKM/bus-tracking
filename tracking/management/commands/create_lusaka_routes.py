from django.core.management.base import BaseCommand
from tracking.models import LusakaRoute, Route, Bus, Stop
import random

class Command(BaseCommand):
    help = 'Create real Lusaka bus routes and stops'

    def handle(self, *args, **options):
        self.stdout.write("Creating Lusaka bus routes...")

        LusakaRoute.objects.all().delete()
        Route.objects.all().delete()
        Bus.objects.all().delete()
        Stop.objects.all().delete()

        routes_data = [
            {
                'route_number': '24',
                'name': 'Matero - Town (City Market)',
                'origin': 'Matero',
                'destination': 'Town (City Market)',
                'waypoints': [
                    [-15.4175, 28.2830], [-15.4200, 28.2850], [-15.4225, 28.2875],
                    [-15.4250, 28.2900], [-15.4300, 28.2950], [-15.4350, 28.3000],
                    [-15.4400, 28.3050], [-15.4450, 28.3100],
                ],
                'stops_list': ['City Market', 'Cairo Road', 'Freedom Way', 'Lumumba Road',
                               'Matero Turnoff', 'Matero Township', 'Matero Market', 'Matero Lilanda']
            },
            {
                'route_number': '52',
                'name': 'Avondale - Town (Millenium)',
                'origin': 'Avondale',
                'destination': 'Town (Millenium)',
                'waypoints': [
                    [-15.4175, 28.2830], [-15.4200, 28.2880], [-15.4225, 28.2930],
                    [-15.4250, 28.2980], [-15.4280, 28.3030], [-15.4310, 28.3080],
                ],
                'stops_list': ['Town (Millenium)', 'Cairo Road', 'Great East Road',
                               'Avondale', 'Marshlands', 'Chelston']
            },
            {
                'route_number': '92',
                'name': 'Chelston - Avondale',
                'origin': 'Chelston',
                'destination': 'Avondale',
                'waypoints': [
                    [-15.4175, 28.2830], [-15.4150, 28.2860], [-15.4125, 28.2890],
                    [-15.4080, 28.2950], [-15.4030, 28.3020], [-15.3980, 28.3090],
                ],
                'stops_list': ['Avondale', 'Great East Road', 'Munali',
                               'Kaunda Square', 'Chelston', 'Chelston Market']
            },
            {
                'route_number': '10',
                'name': 'Kaunda Square - University of Zambia',
                'origin': 'Kaunda Square',
                'destination': 'University of Zambia',
                'waypoints': [
                    [-15.4175, 28.2830], [-15.4150, 28.2860], [-15.4125, 28.2890],
                    [-15.4080, 28.2950], [-15.4030, 28.3020],
                ],
                'stops_list': ['UNZA', 'Great East Road', 'Munali',
                               'Kaunda Square', 'Kaunda Square Stage II']
            },
            {
                'route_number': '51',
                'name': 'Town (Kulima Tower) - Garden Chilulu',
                'origin': 'Town (Kulima Tower)',
                'destination': 'Garden Chilulu',
                'waypoints': [
                    [-15.4175, 28.2830], [-15.4200, 28.2850],
                    [-15.4225, 28.2875], [-15.4250, 28.2900],
                ],
                'stops_list': ['Kulima Tower', 'Freedom Way', 'Cairo Road', 'Garden Chilulu']
            },
        ]

        for route_data in routes_data:
            lusaka_route = LusakaRoute.objects.create(
                route_number=route_data['route_number'],
                name=route_data['name'],
                origin=route_data['origin'],
                destination=route_data['destination'],
                waypoints=route_data['waypoints'],
                stops_list=route_data['stops_list']
            )
            self.stdout.write(f"Created route: {lusaka_route.route_number} - {lusaka_route.name}")

            internal_route = Route.objects.create(
                name=route_data['name'],
                path=route_data['waypoints'],
                waypoints=route_data['waypoints'],
                distance_km=round(random.uniform(5, 15), 1),
                estimated_time=random.randint(20, 60),
                lusaka_route=lusaka_route
            )

            for i, stop_name in enumerate(route_data['stops_list']):
                if i < len(route_data['waypoints']):
                    lat = route_data['waypoints'][i][0]
                    lng = route_data['waypoints'][i][1]
                else:
                    lat = -15.4175
                    lng = 28.2830

                Stop.objects.create(
                    name=stop_name,
                    latitude=lat,
                    longitude=lng,
                    route=internal_route,
                    lusaka_route=lusaka_route,
                    order=i
                )

            for j in range(2):
                bus_num = f"{route_data['route_number']}{j+1}"
                start_lat = route_data['waypoints'][0][0]
                start_lng = route_data['waypoints'][0][1]

                Bus.objects.create(
                    bus_number=f"LUS{bus_num}",
                    route=internal_route,
                    lusaka_route=lusaka_route,
                    current_lat=start_lat,
                    current_lng=start_lng,
                    speed=random.randint(15, 45),
                    capacity=65,
                    occupied_seats=random.randint(20, 55),
                    is_active=True,
                    driver_name=f"Driver {bus_num}",
                    route_progress=random.uniform(0, 0.5),
                    direction=random.choice(['forward', 'reverse'])
                )

        self.stdout.write(self.style.SUCCESS(
            f"Created {LusakaRoute.objects.count()} routes and {Bus.objects.count()} buses"
        ))