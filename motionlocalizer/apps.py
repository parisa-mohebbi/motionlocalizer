# Copyright (c) 2017 The Governors of the University of Alberta

from django.apps import AppConfig
import os
import os.path
import json
import requests


class MotionLocalizerAppConfig(AppConfig):
    name = 'motionlocalizer'
    verbos_name = 'motion localizer'

    def ready(self):
        import motionlocalizer.settings
        localizer_config= os.path.join(os.path.join(motionlocalizer.settings.BASE_DIR, 'config'), 'network_config.txt')
        with open(localizer_config) as f:
            content = f.read()
        if int(json.loads(content)["init_mode"]) == 0:
            config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'static')
            if os.path.isfile(os.path.join(config_dir, 'network_config.txt')):
                with open(os.path.join(config_dir, 'network_config.txt')) as f:
                    content = f.read()

                url_db_config = json.loads(content)['network_config']['config_db_url']
            else:
                url_db_config = json.loads(content)["config_db_url"]

            smartcondo_config = requests.get(url_db_config, {"sensor_type": "MOTION"})
            smartcondo_config = smartcondo_config.json()

            init_sensors(smartcondo_config['sensors'])

            init_gridmap(smartcondo_config['grid'])

            config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'static')
            with open(os.path.join(config_dir, 'network_config.txt'), 'w')as f:
                f.write(json.dumps(smartcondo_config, indent=4))


def init_sensors(sensors):
    from motionlocalizer.models import Sensor
    for sensor in sensors:
        Sensor.objects.update_or_create(sensor_type=sensor['sensor_type'], sensor_id=sensor['sensor_id'],
                                        defaults={'x': sensor['x'],
                                                  'y': sensor['y'], 'z': sensor['z'], 'sensing_area': sensor['sensing_area'],
                                                  'description': sensor['description'], 'hash': sensor['hash']})


def init_gridmap(grid):
    from motionlocalizer.models import GridMap
    GridMap.objects.get_or_create(map=grid)
    # print(GridMap.objects.all()[0].grid)
