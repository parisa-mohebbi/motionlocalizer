# Copyright (c) 2017 The Governors of the University of Alberta

from motionlocalizer.models import *
import time as pythonTimer
import requests
import motionlocalizer.settings
import os
import json
from django.http import HttpResponse, JsonResponse
import threading
from localization.localization import Localizer


def send_event(request):
    source = request.GET.get('source')
    timestamp = float(request.GET.get('timestamp'))
    sensor_hash = request.GET.get('sensor_hash')
    person_hash = request.GET.get('person_hash', 'no_person')
    data = request.GET.get('data')

    post_event = [{'source': source, 'timestamp': timestamp, 'sensor_hash': sensor_hash, 'person_hash': person_hash,
                  'data': data}]

    config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'static')
    with open(os.path.join(config_dir, 'network_config.txt')) as f:
        content = f.read()

    event_db_url = json.loads(content)['network_config']['event_db_url']

    post_field = {'events': json.dumps(post_event)}

    res = requests.get(event_db_url, post_field)
    #import logging
    #logging.getLogger('django').log(logging.ERROR, res)
    event_hash = res.json()['hash']

    if source == 'MOTION':
        Event.objects.create(source=source, timestamp=timestamp, sensor=Sensor.objects.get(hash=sensor_hash),
                             data=int(data), hash=event_hash[0])

    return HttpResponse('successful')


def start_localizing(request):
    threading.Thread(target=run_localization).start()
    return JsonResponse({'response': 'successful'})


def get_config(request):
    config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'static')
    with open(os.path.join(config_dir, 'network_config.txt')) as f:
        content = f.read()

    smartcondo_config = json.loads(content)
    localizer_network_config_data = parse_config()

    for key in localizer_network_config_data:
        smartcondo_config['network_config'][key] = localizer_network_config_data[key]

    response = smartcondo_config
    response = json.dumps(response)
    return HttpResponse(response)


def run_localization():
    starttime = pythonTimer.time()
    while True:
        Localizer(pythonTimer.time()).run()
        pythonTimer.sleep(1.0 - ((pythonTimer.time() - starttime) % 1.0))


def parse_config():
    config_dir = os.path.join(motionlocalizer.settings.BASE_DIR, 'config')
    with open(os.path.join(config_dir, 'network_config.txt')) as f:
        content = f.read()
    config_data = json.loads(content)
    return config_data
