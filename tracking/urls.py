from django.urls import path
from . import views

urlpatterns = [
    # Frontend
    path('', views.index, name='index'),

    # Buses and Stops
    path('api/stops/', views.get_all_stops, name='all-stops'),
    path('api/live-buses/', views.get_all_buses, name='live-buses'),
    path('api/buses/<int:bus_id>/', views.get_bus_detail, name='bus-detail'),
    path('api/routes/<int:route_id>/path/', views.get_route_path, name='route-path'),
    path('api/passengers/nearby-buses/', views.find_nearby_buses, name='nearby-buses'),

    # Lusaka Routes
    path('api/lusaka-routes/', views.get_lusaka_routes, name='lusaka-routes'),
    path('api/lusaka-routes/<int:route_id>/buses/', views.get_buses_on_route, name='buses-on-route'),

    # Ride Request Feature
    path('api/rides/request/', views.request_ride, name='request-ride'),
    path('api/rides/<int:ride_id>/tracking/', views.get_ride_tracking, name='ride-tracking'),
    path('api/rides/tracking/start/', views.start_ride_tracking, name='start-ride-tracking'),
    path('api/rides/<int:ride_id>/rate/', views.rate_ride, name='rate-ride'),

    # Notifications
    path('api/notifications/<int:passenger_id>/', views.get_notifications, name='notifications'),

    # Bus Movement
    path('api/buses/movement/start-all/', views.start_route_simulation, name='start-all'),
]