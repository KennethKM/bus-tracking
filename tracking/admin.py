from django.contrib import admin
from .models import (
    Route,
    Stop,
    Bus,
    Passenger,
    WaitingRequest,
    Driver,
    DriverBusAssignment
)



admin.site.register(Route)
admin.site.register(Stop)
admin.site.register(Bus)
admin.site.register(Passenger)
admin.site.register(WaitingRequest)
admin.site.register(Driver)
admin.site.register(DriverBusAssignment)