from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Frontend
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/stops/', views.get_all_stops, name='all-stops'),
    path('api/live-buses/', views.get_all_buses, name='live-buses'),
    path('api/passengers/nearby-buses/', views.find_nearby_buses, name='nearby-buses'),
]