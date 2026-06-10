import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_tracking_system.settings')
django.setup()

from tracking.models import Route, Bus, Stop, Passenger
from django.contrib.auth.models import User

print("="*50)
print("Setting up Lusaka Bus Tracking System...")
print("="*50)

# Clear existing data
Bus.objects.all().delete()
Stop.objects.all().delete()
Route.objects.all().delete()
Passenger.objects.all().delete()

# Create routes
print("Creating routes...")
r1 = Route.objects.create(
    name='Route 1: Town to Matero',
    path=[[-15.3875, 28.3228], [-15.3950, 28.3150], [-15.4025, 28.3075], [-15.4100, 28.3000], [-15.4175, 28.2950]]
)
r2 = Route.objects.create(
    name='Route 2: Town to Chelston',
    path=[[-15.3875, 28.3228], [-15.3800, 28.3300], [-15.3725, 28.3375], [-15.3650, 28.3450]]
)
r3 = Route.objects.create(
    name='Route 3: Town to Kalingalinga',
    path=[[-15.3875, 28.3228], [-15.3950, 28.3350], [-15.4025, 28.3475], [-15.4100, 28.3600]]
)

print(f"✓ Created {Route.objects.count()} routes")

# Create stops
print("Creating stops...")
stops_data = [
    ('Lusaka City Market', -15.4150, 28.2800, r1, 1),
    ('Cairo Road', -15.4200, 28.2850, r1, 2),
    ('Matero Shopping Centre', -15.4250, 28.2900, r1, 3),
    ('Matero Police', -15.4300, 28.2950, r1, 4),
    ('Arcades Mall', -15.3900, 28.3250, r1, 5),
    ('Chelston School', -15.3700, 28.3400, r2, 3),
    ('Chelston Market', -15.3650, 28.3450, r2, 4),
    ('East Park Mall', -15.4000, 28.3300, r2, 5),
    ('Kalingalinga Police', -15.4050, 28.3500, r3, 3),
    ('Kalingalinga Market', -15.4100, 28.3600, r3, 4),
]

for name, lat, lng, route, order in stops_data:
    Stop.objects.create(name=name, latitude=lat, longitude=lng, route=route, order=order)

print(f"✓ Created {Stop.objects.count()} stops")

# Create buses
print("Creating buses...")
buses_data = [
    ('LUS001', r1, -15.3875, 28.3228, 35, 32),
    ('LUS002', r1, -15.3950, 28.3150, 42, 45),
    ('LUS003', r1, -15.4100, 28.3000, 38, 28),
    ('LUS004', r2, -15.3800, 28.3300, 40, 55),
    ('LUS005', r2, -15.3650, 28.3450, 36, 38),
    ('LUS006', r3, -15.3950, 28.3350, 45, 42),
    ('LUS007', r3, -15.4100, 28.3600, 33, 50),
]

for number, route, lat, lng, speed, occupied in buses_data:
    Bus.objects.create(
        bus_number=number,
        route=route,
        current_lat=lat,
        current_lng=lng,
        speed=speed,
        capacity=65,
        occupied_seats=occupied,
        is_active=True
    )

print(f"✓ Created {Bus.objects.count()} buses")

# Create test passenger
print("Creating test passenger...")
user, created = User.objects.get_or_create(
    username='passenger1',
    defaults={'password': 'pass123456'}
)
Passenger.objects.create(
    user=user,
    phone_number='+260971234567',
    current_lat=-15.4200,
    current_lng=28.2850
)

print("✓ Created test passenger")

# Summary
print("\n" + "="*50)
print("✅ LUSAKA BUS TRACKING SYSTEM IS READY!")
print("="*50)
print(f"📊 Routes: {Route.objects.count()}")
print(f"📍 Stops: {Stop.objects.count()}")
print(f"🚌 Buses: {Bus.objects.count()}")
print(f"👥 Passengers: {Passenger.objects.count()}")
print("="*50)
print("\n🎯 Next steps:")
print("   1. Run: python manage.py runserver")
print("   2. Open: http://127.0.0.1:8000")
print("   3. Allow location access when prompted")
print("   4. Click 'Find Buses Near Me' button")
print("="*50)