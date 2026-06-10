from tracking.models import Bus, Stop


def move_buses():

    buses = Bus.objects.all()

    for bus in buses:

        stops = list(
            Stop.objects.filter(
                route=bus.route
            ).order_by("order")
        )

        if not stops:
            continue

        next_index = (
            bus.current_stop_index + 1
        ) % len(stops)

        next_stop = stops[next_index]

        bus.current_lat = next_stop.latitude
        bus.current_lng = next_stop.longitude

        bus.current_stop_index = next_index

        bus.save()