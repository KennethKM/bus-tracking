from django.core.management.base import BaseCommand
import time

from tracking.models import Bus, Stop


class Command(BaseCommand):
    help = 'Simulate buses moving along their routes'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting bus simulation..."))

        while True:
            buses = Bus.objects.all()

            for bus in buses:
                stops = Stop.objects.filter(route=bus.route).order_by('order')

                if not stops.exists():
                    continue

                # Move to next stop (loop back to start)
                bus.current_stop_index = (bus.current_stop_index + 1) % len(stops)

                next_stop = stops[bus.current_stop_index]

                bus.current_lat = next_stop.latitude
                bus.current_lng = next_stop.longitude
                bus.save()

                self.stdout.write(
                    f"Bus {bus.id} moved to {next_stop.name} "
                    f"({bus.current_lat}, {bus.current_lng})"
                )

            # Wait before next movement
            time.sleep(5)