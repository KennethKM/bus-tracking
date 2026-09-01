import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from tracking.models import Trip, Stop, StopTime


class Command(BaseCommand):
    help = "Import GTFS stop_times.txt"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "gtfs",
            "stop_times.txt"
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

                trip = Trip.objects.filter(
                    trip_id=row["trip_id"]
                ).first()

                stop = Stop.objects.filter(
                    stop_id=int(row["stop_id"])
                ).first()

                if trip is None or stop is None:
                    skipped += 1
                    continue

                stop_time, created = StopTime.objects.update_or_create(
                    trip=trip,
                    stop_sequence=int(row["stop_sequence"]),
                    defaults={
                        "stop": stop,
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