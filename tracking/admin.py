from django.contrib import admin
from .models import Route, Stop, Bus

admin.site.register(Route)
admin.site.register(Stop)
admin.site.register(Bus)