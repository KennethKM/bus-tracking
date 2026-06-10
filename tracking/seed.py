from .models import Route, Stop, Bus

def run():
    Route.objects.all().delete()
    Stop.objects.all().delete()
    Bus.objects.all().delete()

    # ===================== ROUTES =====================
    route1 = Route.objects.create(name="Kanyama - City Market")
    route2 = Route.objects.create(name="Chawama - Town")
    route3 = Route.objects.create(name="UNZA - Town")

    # ===================== STOPS =====================

    # KANYAMA ROUTE
    Stop.objects.create(route=route1, name="Kanyama Terminus", latitude=-15.455, longitude=28.250, order=1)
    Stop.objects.create(route=route1, name="Matero", latitude=-15.410, longitude=28.280, order=2)
    Stop.objects.create(route=route1, name="City Market", latitude=-15.416, longitude=28.283, order=3)

    # CHAWAMA ROUTE
    Stop.objects.create(route=route2, name="Chawama", latitude=-15.470, longitude=28.260, order=1)
    Stop.objects.create(route=route2, name="Kamwala", latitude=-15.420, longitude=28.290, order=2)
    Stop.objects.create(route=route2, name="Town", latitude=-15.416, longitude=28.283, order=3)

    # UNZA ROUTE
    Stop.objects.create(route=route3, name="UNZA", latitude=-15.392, longitude=28.328, order=1)
    Stop.objects.create(route=route3, name="Showgrounds", latitude=-15.420, longitude=28.310, order=2)
    Stop.objects.create(route=route3, name="Town", latitude=-15.416, longitude=28.283, order=3)

    # ===================== BUSES =====================
    Bus.objects.create(route=route1, current_lat=-15.455, current_lng=28.250, speed=35)
    Bus.objects.create(route=route2, current_lat=-15.470, current_lng=28.260, speed=30)
    Bus.objects.create(route=route3, current_lat=-15.392, current_lng=28.328, speed=40)

    print("Seed data created successfully!")