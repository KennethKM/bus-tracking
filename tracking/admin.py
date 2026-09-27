from django.contrib import admin
from django.utils import timezone
from .models import Route, Stop, Bus, Driver, RouteRequest


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'origin', 'destination')


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'route', 'order')


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'registration_number', 'route', 'is_active')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'license_number', 'assigned_bus_display', 'is_active')
    search_fields = ('name', 'license_number')
    list_filter = ('is_active',)
    actions = ['unassign_bus']

    def assigned_bus_display(self, obj):
        if not obj.assigned_bus:
            return ""
        bus = obj.assigned_bus
        # Use the current APPROVED RouteRequest.route if one exists for this driver + bus.
        approved_request = RouteRequest.objects.filter(
            driver=obj,
            bus=bus,
            status=RouteRequest.STATUS_APPROVED,
        ).order_by('-approved_at').first()
        if approved_request and approved_request.route:
            return f"Bus {bus.id} to {approved_request.route.name}"
        return f"Bus {bus.id}"

    assigned_bus_display.short_description = 'Assigned bus'

    def unassign_bus(self, request, queryset):
        updated = queryset.update(assigned_bus=None)
        if request is not None:
            self.message_user(request, f'Unassigned bus from {updated} driver(s).')
        return updated

    unassign_bus.short_description = 'Unassign selected driver(s)'


@admin.register(RouteRequest)
class RouteRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'bus_short', 'route', 'status', 'requested_at', 'approved_at')
    list_filter = ('status',)
    search_fields = ('driver__name', 'route__name', 'bus__registration_number')
    actions = ['approve_selected', 'reject_selected']

    def bus_short(self, obj):
        if not obj.bus:
            return ""
        return f"Bus {obj.bus.id}"

    bus_short.short_description = 'Buses'

    def approve_selected(self, request, queryset):
        for route_request in queryset.filter(status=RouteRequest.STATUS_PENDING):
            route_request.status = RouteRequest.STATUS_APPROVED
            route_request.approved_at = timezone.now()
            route_request.bus.route = route_request.route
            route_request.bus.save(update_fields=['route'])
            route_request.save(update_fields=['status', 'approved_at'])

    approve_selected.short_description = 'Approve selected pending requests'

    def reject_selected(self, request, queryset):
        queryset.filter(status=RouteRequest.STATUS_PENDING).update(status=RouteRequest.STATUS_REJECTED)

    reject_selected.short_description = 'Reject selected pending requests'