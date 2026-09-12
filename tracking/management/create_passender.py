from django.core.management.base import BaseCommand
from tracking.models import Passenger
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a test passenger'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='passenger1',
            defaults={'password': 'testpass123'}
        )
        
        passenger, created = Passenger.objects.get_or_create(
            id=1,
            defaults={
                'user': user,
                'phone_number': '+260971234567',
                'full_name': 'Test Passenger',
                'current_lat': -15.397792,
                'current_lng': 28.333757
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Passenger created: {passenger.full_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️ Passenger already exists: {passenger.full_name}'))