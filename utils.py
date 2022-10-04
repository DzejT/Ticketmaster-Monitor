import os
import sys
import json
from random import randint

def get_settings():
    headers_file = 'settings.json'

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    config_path = os.path.join(application_path, headers_file)

    # settings
    settings = []
    try:
        with open(config_path, 'r+') as f:
            settings = json.load(f)
    except:
        print('No settings.json file found!')

    return settings

def get_proxy_file():
    proxy_file = 'proxies.txt'

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    config_path = os.path.join(application_path, proxy_file)

    # proxies
    proxies = []
    try:
        with open(config_path, 'r+') as f:
            proxies = f.readlines()
    except:
        print('No proxies.txt file found!')

    return proxies


def get_proxy(proxies, https=True):
    if not proxies:
        return

    prox = proxies[randint(0, len(proxies) - 1)].rstrip('\n')
    prox_info = prox.split(':')
    if https:
        return {'https': 'http://' + prox_info[2] + ':' + prox_info[3] + '@' + prox_info[0] + ':' + prox_info[1]}
    else:
        return {'http': 'http://' + prox_info[2] + ':' + prox_info[3] + '@' + prox_info[0] + ':' + prox_info[1]}