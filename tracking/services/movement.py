import threading
import time
from tracking.models import Bus

running = False

def move_buses():
    global running
    running = True

    while running:
        buses = Bus.objects.all()

        for b in buses:
            b.current_lat += 0.0001
            b.current_lng += 0.0001
            b.save()

        time.sleep(3)


def start():
    thread = threading.Thread(target=move_buses)
    thread.daemon = True
    thread.start()


def stop():
    global running
    running = False