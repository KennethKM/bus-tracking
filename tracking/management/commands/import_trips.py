import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from tracking.models import Route, Trip


class Command(BaseCommand):
    help = "Import GTFS trips.txt"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "gtfs",
            "trips.txt"
        )

        imported = 0
        updated = 0
        skipped = 0

        with open(
            file_path,
            encoding="utf-8",
            newline=""
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:

                route = Route.objects.filter(
                    route_id=row["route_id"]
                ).first()

                if route is None:
                    skipped += 1
                    continue

                trip, created = Trip.objects.update_or_create(
                    trip_id=row["trip_id"],
                    defaults={
                        "route": route,
                        "trip_headsign": row["trip_headsign"],
                        "direction_id": int(row["direction_id"]),
                        "shape_id": row["shape_id"],
                        "service_id": row["service_id"],
                    }
                )

                if created:
                    imported += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {imported}, Updated: {updated}, Skipped: {skipped}"
            )
        )