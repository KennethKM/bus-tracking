import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from tracking.models import Shape


class Command(BaseCommand):
    help = "Import GTFS shapes.txt"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "gtfs",
            "shapes.txt"
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

                shape, created = Shape.objects.update_or_create(
                    shape_id=row["shape_id"],
                    shape_pt_sequence=int(row["shape_pt_sequence"]),
                    defaults={
                        "shape_pt_lat": float(row["shape_pt_lat"]),
                        "shape_pt_lon": float(row["shape_pt_lon"]),
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