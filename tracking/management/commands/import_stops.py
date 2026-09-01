import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from tracking.models import Stop


class Command(BaseCommand):
    help = "Import GTFS stops.txt"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "gtfs",
            "stops.txt"
        )

        imported = 0
        updated = 0

        with open(
            file_path,
            encoding="utf-8",
            newline=""
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:

                if (
                    not row["stop_lat"].strip()
                    or not row["stop_lon"].strip()
                ):
                    continue
                
                stop, created = Stop.objects.update_or_create(
                    stop_id=int(row["stop_id"]),
                    defaults={
                        "stop_name": row["stop_name"],
                        "stop_lat": float(row["stop_lat"]),
                        "stop_lon": float(row["stop_lon"]),
                    }
                )

                if created:
                    imported += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {imported}, Updated: {updated}"
            )
        )