import csv
import json
import os
import zipfile
from io import StringIO

from django.core.management.base import BaseCommand

from tracking.models import Route


DEFAULT_GTFS_PATH = '/mnt/data/gtfs.zip'


def get_gtfs_zip_path():
    env_path = os.environ.get('GTFS_ZIP_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    project_root_path = os.path.join(os.getcwd(), 'gtfs.zip')
    if os.path.exists(project_root_path):
        return project_root_path

    if os.path.exists(DEFAULT_GTFS_PATH):
        return DEFAULT_GTFS_PATH

    return None


class Command(BaseCommand):
    help = 'Generate a static JSON file mapping application Route.id -> GTFS shape coordinates (if available).'

    def handle(self, *args, **options):
        zip_path = get_gtfs_zip_path()
        if not zip_path or not os.path.exists(zip_path):
            self.stdout.write(self.style.WARNING('GTFS zip not found; aborting shape generation.'))
            return

        with zipfile.ZipFile(zip_path) as zf:
            def _read_csv(name):
                if name not in zf.namelist():
                    return []
                text = zf.read(name).decode('utf-8-sig', 'replace')
                return [dict(r) for r in csv.DictReader(StringIO(text))]

            shapes = _read_csv('shapes.txt')
            trips = _read_csv('trips.txt')
            routes = _read_csv('routes.txt')

        # Build shape_id -> ordered list of (lat, lng)
        shape_points = {}
        for row in shapes:
            sid = (row.get('shape_id') or '').strip()
            if not sid:
                continue
            try:
                seq = int(row.get('shape_pt_sequence') or 0)
            except Exception:
                seq = 0
            lat = row.get('shape_pt_lat')
            lon = row.get('shape_pt_lon')
            try:
                latf = float(lat)
                lonf = float(lon)
            except Exception:
                continue
            shape_points.setdefault(sid, []).append((seq, latf, lonf))

        for sid, pts in list(shape_points.items()):
            pts.sort(key=lambda t: t[0])
            shape_points[sid] = [[p[1], p[2]] for p in pts]

        # Map trip_id -> shape_id
        trip_shape = {}
        for row in trips:
            tid = (row.get('trip_id') or '').strip()
            sid = (row.get('shape_id') or '').strip()
            rid = (row.get('route_id') or '').strip()
            if tid and sid:
                trip_shape[tid] = sid

        # For each GTFS route_id, pick the first trip's shape (if any)
        route_to_shape = {}
        # Build route_name as importer does so we can match application Route
        for row in routes:
            route_id = (row.get('route_id') or '').strip()
            if not route_id:
                continue
            route_name = (row.get('route_long_name') or row.get('route_short_name') or route_id).strip()
            # find a trip for this route that has a shape
            chosen_shape = None
            for t in trips:
                if (t.get('route_id') or '').strip() != route_id:
                    continue
                tid = (t.get('trip_id') or '').strip()
                sid = trip_shape.get(tid)
                if sid and sid in shape_points:
                    chosen_shape = shape_points[sid]
                    break
            if chosen_shape:
                # find application Route by name
                app_route = Route.objects.filter(name=route_name).first()
                if app_route:
                    route_to_shape[str(app_route.id)] = {
                        'id': app_route.id,
                        'name': app_route.name,
                        'shape': chosen_shape
                    }

        # Ensure static folder exists
        static_dir = os.path.join(os.getcwd(), 'tracking', 'static', 'tracking')
        os.makedirs(static_dir, exist_ok=True)
        out_path = os.path.join(static_dir, 'route_shapes.json')
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(route_to_shape, fh, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f'Wrote route shapes for {len(route_to_shape)} routes to {out_path}'))
