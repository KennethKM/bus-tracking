import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from tracking.models import Route


class Command(BaseCommand):

    help = "Import routes from GTFS routes.txt"

    def handle(self, *args, **options):

        file_path = (
            Path(settings.BASE_DIR)
            / "gtfs"
            / "routes.txt"
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

                route, created = (
                    Route.objects.update_or_create(
                        route_id=row["route_id"],
                        defaults={
                            "route_long_name":
                                row["route_long_name"],

                            "continuous_pickup":
                                int(
                                    row.get(
                                        "continuous_pickup",
                                        0
                                    ) or 0
                                ),

                            "continuous_drop_off":
                                int(
                                    row.get(
                                        "continuous_drop_off",
                                        0
                                    ) or 0
                                ),
                        }
                    )
                )

                if created:
                    imported += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {imported}, "
                f"Updated: {updated}"
            )
        )