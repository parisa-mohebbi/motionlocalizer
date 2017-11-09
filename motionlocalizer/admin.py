# Copyright (c) 2017 The Governors of the University of Alberta

from django.contrib import admin
from motionlocalizer.models import Sensor, Event, GridMap


class SensorAdmin(admin.ModelAdmin):
    model = Sensor


class EventAdmin(admin.ModelAdmin):
    model = Event


class GridMapAdmin(admin.ModelAdmin):
    model = GridMap

admin.site.register(Sensor, SensorAdmin)
admin.site.register(Event,EventAdmin)
admin.site.register(GridMap,GridMapAdmin)