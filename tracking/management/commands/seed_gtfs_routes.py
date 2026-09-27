import csv
import os
import zipfile
from io import StringIO

from django.core.management.base import BaseCommand

from tracking.models import Route, Stop


DEFAULT_GTFS_PATH = '/mnt/data/gtfs.zip'


def get_gtfs_zip_path():
    # Allow overriding via environment for CI or custom paths
    env_path = os.environ.get('GTFS_ZIP_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # Prefer project-root gtfs.zip (run from project root with manage.py)
    project_root_path = os.path.join(os.getcwd(), 'gtfs.zip')
    if os.path.exists(project_root_path):
        return project_root_path

    # Fallback to /mnt/data
    if os.path.exists(DEFAULT_GTFS_PATH):
        return DEFAULT_GTFS_PATH

    return None


class Command(BaseCommand):
    help = 'Import GTFS route and stop data into the existing Route and Stop tables without creating a second GTFS schema.'

    def handle(self, *args, **options):
        zip_path = get_gtfs_zip_path()
        if not zip_path:
            self.stdout.write(self.style.WARNING('GTFS zip not found at /mnt/data/gtfs.zip; no data imported.'))
            return

        if not os.path.exists(zip_path):
            self.stdout.write(self.style.WARNING(f'GTFS zip not found: {zip_path}'))
            return

        with zipfile.ZipFile(zip_path) as zf:
            route_rows = self._read_csv(zf, 'routes.txt')
            stop_rows = self._read_csv(zf, 'stops.txt')

            trip_rows = self._read_csv(zf, 'trips.txt')
            stop_time_rows = self._read_csv(zf, 'stop_times.txt')

            route_map = {}
            for row in route_rows:
                route_id = (row.get('route_id') or '').strip()
                if not route_id:
                    continue
                route_name = (row.get('route_long_name') or row.get('route_short_name') or route_id).strip()
                route_obj, created = Route.objects.get_or_create(
                    name=route_name,
                    defaults={
                        'origin': '',
                        'destination': '',
                    },
                )
                route_map[route_id] = route_obj

            stop_map = {}
            for row in stop_rows:
                stop_id = (row.get('stop_id') or '').strip()
                if not stop_id:
                    continue
                stop_name = (row.get('stop_name') or stop_id).strip()
                stop_lat = row.get('stop_lat')
                stop_lon = row.get('stop_lon')
                try:
                    latitude = float(stop_lat)
                    longitude = float(stop_lon)
                except (TypeError, ValueError):
                    continue
                stop_map[stop_id] = {
                    'name': stop_name,
                    'latitude': latitude,
                    'longitude': longitude,
                }

            ordered_stop_ids_by_route = {}
            if trip_rows and stop_time_rows:
                trip_stop_sequence = {}
                for row in stop_time_rows:
                    trip_id = (row.get('trip_id') or '').strip()
                    stop_id = (row.get('stop_id') or '').strip()
                    sequence = row.get('stop_sequence')
                    try:
                        seq_value = int(sequence)
                    except (TypeError, ValueError):
                        seq_value = 100000
                    trip_stop_sequence.setdefault(trip_id, {})[stop_id] = seq_value

                for row in trip_rows:
                    trip_route_id = (row.get('route_id') or '').strip()
                    trip_id = (row.get('trip_id') or '').strip()
                    if not trip_route_id or not trip_id:
                        continue
                    route_obj = route_map.get(trip_route_id)
                    if not route_obj:
                        continue
                    route_sequence = trip_stop_sequence.get(trip_id, {})
                    ordered_stop_ids_by_route.setdefault(route_obj.id, [])
                    ordered = [stop_id for stop_id, _ in sorted(route_sequence.items(), key=lambda item: item[1])]
                    if ordered:
                        ordered_stop_ids_by_route[route_obj.id].extend(ordered)

            for route_obj in Route.objects.all():
                route_stop_ids = ordered_stop_ids_by_route.get(route_obj.id, [])
                if not route_stop_ids:
                    continue
                seen = set()
                for order_index, stop_id in enumerate(route_stop_ids, start=1):
                    if stop_id in seen:
                        continue
                    seen.add(stop_id)
                    stop_data = stop_map.get(stop_id)
                    if not stop_data:
                        continue
                    Stop.objects.get_or_create(
                        route=route_obj,
                        name=stop_data['name'],
                        defaults={
                            'latitude': stop_data['latitude'],
                            'longitude': stop_data['longitude'],
                            'order': order_index,
                        },
                    )

            for route_obj in Route.objects.all():
                route_stops = list(Stop.objects.filter(route=route_obj).order_by('order', 'id'))
                for order_index, stop in enumerate(route_stops, start=1):
                    if stop.order != order_index:
                        stop.order = order_index
                        stop.save(update_fields=['order'])

        self.stdout.write(self.style.SUCCESS(f'GTFS import complete: {Route.objects.count()} routes and {Stop.objects.count()} stops.'))

    def _read_csv(self, zf, filename):
        if filename not in zf.namelist():
            return []
        text = zf.read(filename).decode('utf-8-sig', 'replace')
        reader = csv.DictReader(StringIO(text))
        return [dict(row) for row in reader]
