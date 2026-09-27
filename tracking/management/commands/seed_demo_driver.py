from django.core.management.base import BaseCommand
from tracking.models import Driver, Bus


class Command(BaseCommand):
    help = 'Create the demo driver and assigned bus if they do not already exist.'

    def handle(self, *args, **options):
        bus, _ = Bus.objects.get_or_create(
            registration_number='ABC123',
            defaults={
                'route': None,
                'capacity': 40,
                'current_lat': 0.0,
                'current_lng': 0.0,
                'current_stop_index': 0,
                'speed': 0,
                'is_active': False,
            },
        )

        driver, _ = Driver.objects.get_or_create(
            name='Driver 1',
            defaults={
                'license_number': 'A12345',
                'assigned_bus': bus,
                'is_active': True,
            },
        )

        driver.license_number = 'A12345'
        driver.assigned_bus = bus
        driver.is_active = True
        driver.save(update_fields=['license_number', 'assigned_bus', 'is_active'])

        bus.registration_number = 'ABC123'
        bus.route = None
        bus.current_lat = 0.0
        bus.current_lng = 0.0
        bus.is_active = False
        bus.save(update_fields=['registration_number', 'route', 'current_lat', 'current_lng', 'is_active'])

        self.stdout.write(self.style.SUCCESS(
            f"Demo driver ready: {driver} | Bus: {bus.registration_number} | Route: unassigned"
        ))
