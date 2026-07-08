from django.urls import path
from . import views

urlpatterns = [
    # Frontend
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/stops/', views.get_all_stops, name='all-stops'),
    path('api/live-buses/', views.get_all_buses, name='live-buses'),
    path('api/buses/<int:bus_id>/', views.get_bus_detail, name='bus-detail'),
    path('api/buses/<int:bus_id>/eta-stop/<int:stop_id>/', views.get_bus_eta_to_stop, name='bus-eta'),
    path('api/routes/<int:route_id>/path/', views.get_route_path, name='route-path'),
    path('api/passengers/nearby-buses/', views.find_nearby_buses, name='nearby-buses'),
    path('api/trips/request/', views.request_trip, name='request-trip'),
    path('api/trips/<int:trip_id>/status/', views.get_trip_status, name='trip-status'),
    path('api/trips/<int:trip_id>/rate/', views.rate_trip, name='rate-trip'),
    path('api/notifications/<int:passenger_id>/', views.get_notifications, name='notifications'),
    
    # NEW: Bus movement tracking endpoints
    path('api/buses/movement/simulate/', views.simulate_bus_movement, name='simulate-movement'),
    path('api/buses/<int:bus_id>/movement/', views.get_bus_movement, name='bus-movement'),
    path('api/trips/tracking/start/', views.start_trip_tracking, name='start-tracking'),
    path('api/trips/<int:trip_id>/tracking/', views.get_trip_tracking, name='trip-tracking'),
]