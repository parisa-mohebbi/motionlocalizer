# Copyright (c) 2017 The Governors of the University of Alberta

from motionlocalizer.models import *
import threading
import os
import motionlocalizer.settings
import json
import requests
from shapely.geometry import Polygon
from shapely.ops import cascaded_union


class Localizer(threading.Thread):
    to_be_localized_queue = []
    localizer_lock = threading.Lock()

    def __init__(self, time):
        threading.Thread.__init__(self)
        self.time = time

    def run(self):
        Localizer.to_be_localized_queue.append(self.time)
        with Localizer.localizer_lock:
            while len(Localizer.to_be_localized_queue) > 0:
                timestamp = Localizer.to_be_localized_queue[0]
                Localizer.to_be_localized_queue = Localizer.to_be_localized_queue[1:]
                output = self.localize(timestamp)
                config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'static')
                with open(os.path.join(config_dir, 'network_config.txt')) as f:
                    content = f.read()

                    confidence_map_db_url = json.loads(content)['network_config']['confidence_map_db_url']
                # print('*************output--------------------%s' % str(output))
                if output:
                    requests.get(url=confidence_map_db_url, json=output)

    def localizer_confidence(self):
        return 0.9

    # When motion localizer wants to localize for time t, it looks at the events in [t-T to t] to check
    #  if a movement was done. This function returns T in second
    def get_event_period(self):
        return 1.0

    def localize(self, time):
        fired_sensors = self.extract_fired_sensors(time-self.get_event_period(), time)
        if len(fired_sensors) == 0:
            return

        grid_map = json.loads(GridMap.objects.last().map)

        confidenceMap = []

        for g in grid_map:

            square = Polygon([tuple(x) for x in g])
            for sensor in fired_sensors:
                #print(sensor)
                #print(time)
                already_added = [sq for sq in confidenceMap if self.is_same_square(sq[0], g)]
                if len(already_added) > 1:
                    raise BaseException('localizer(): This really should not happen!')

                json_acceptable_string = sensor.sensing_area.replace("'", "\"")
                sensing_area = Polygon([tuple(x) for x in json.loads(json_acceptable_string)['points']])
                if square.intersection(sensing_area).area > 0.01:
                    if len(already_added) == 1:
                        already_added[0][1] += 1
                        #print('already added')
                    else:
                        confidenceMap.append([g, 1])
                else:
                    if len(already_added) == 1:
                        already_added[0][1] += 0
                    else:
                        confidenceMap.append([g, 0])

        self.normalize_confMap(confidenceMap)
        estimate_loc, confidence = self.get_estimate(confidenceMap)
        return {'timestamp': time, 'source': 'MOTION', 'map': json.dumps(confidenceMap),
                'source_confidence': self.localizer_confidence(),
                'estimate_confidence': confidence,
                'estimated_loc_x': estimate_loc[0],
                'estimated_loc_y': estimate_loc[1]}

    def is_same_square(self, s1, s2):
        return abs(s1[0][0] - s2[0][0]) < 0.001 and \
               abs(s1[0][1] - s2[0][1]) < 0.001 and \
               abs(s1[1][0] - s2[1][0]) < 0.001 and \
               abs(s1[1][1] - s2[1][1]) < 0.001 and \
               abs(s1[2][0] - s2[2][0]) < 0.001 and \
               abs(s1[2][1] - s2[2][1]) < 0.001 and \
               abs(s1[3][0] - s2[3][0]) < 0.001 and \
               abs(s1[3][1] - s2[3][1]) < 0.001

    def normalize_confMap(self, confidenceMap):
        summation = sum([x[1] for x in confidenceMap])
        for square in confidenceMap:
            square[1] = float(square[1]) / float(summation)

    def get_estimate(self, confidenceMap):
        max_prob = max([x[1] for x in confidenceMap])
        estimate_area = []
        num_of_squares = 0
        for square in confidenceMap:
            if abs(square[1] - max_prob) < 0.001:
                estimate_area.append(Polygon([tuple(x) for x in square[0]]))
                num_of_squares += 1
        union = cascaded_union(estimate_area)
        return [union.centroid.x, union.centroid.y], max_prob*num_of_squares

    #
    def extract_fired_sensors(self, start, end):
        sensors = Sensor.objects.all()
        fired_sensors = []
        for s in sensors:
            if Event.objects.filter(timestamp__gt=start, timestamp__lt=end, sensor=s).exists():
                fired_sensors.append(s)
                continue
            if Event.objects.filter(sensor=s).exists():
                last_event = Event.objects.filter(sensor=s).latest(field_name='timestamp')
                if int(last_event.data) == 1:
                    # print('latest is 1')
                    # print(s)
                    fired_sensors.append(s)

        return fired_sensors
