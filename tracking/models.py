from django.db import models

class Route(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Stop(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    order = models.IntegerField()

    def __str__(self):
        return self.name


class Bus(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    current_lat = models.FloatField()
    current_lng = models.FloatField()
    current_stop_index = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Buses"

    def __str__(self):
        return f"Bus {self.id} on {self.route.name}"