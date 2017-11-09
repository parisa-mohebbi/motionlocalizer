# Copyright (c) 2017 The Governors of the University of Alberta

from django.db import models


class Sensor(models.Model):
    sensor_type = models.CharField(max_length=50)
    sensor_id = models.CharField(max_length=100)  # for motions: Pi_id,node_id,sensor_id / for estimotes: identifier
    x = models.FloatField(null=True)
    y = models.FloatField(null=True)
    z = models.FloatField(null=True, default=0.0)
    sensing_area = models.TextField(null=True)
    description = models.TextField(null=True)
    hash = models.CharField(max_length=20, db_index=True, unique=True)

    def __str__(self):
        return '%s, id: %s, %s'%(self.sensor_type, self.sensor_id, self.description)


class Event(models.Model):
    source = models.CharField(max_length=50)
    timestamp = models.FloatField()
    sensor = models.ForeignKey(Sensor)
    data = models.IntegerField()
    hash = models.CharField(max_length=20)

    def __str__(self):
        return 'time: %s --> sensor: <%s>", data: %s' % (
        str(self.timestamp), str(self.sensor), str(self.data))


class GridMap(models.Model):
    map = models.TextField()