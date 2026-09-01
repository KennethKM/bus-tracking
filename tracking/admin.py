from django.contrib import admin
from .models import (
    Route,
    Stop,
    Bus,
    Passenger,
    WaitingRequest
)



admin.site.register(Route)
admin.site.register(Stop)
admin.site.register(Bus)
admin.site.register(Passenger)
admin.site.register(WaitingRequest)