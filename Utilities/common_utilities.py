from pathlib import Path
import platform
import datetime
import math
import socket
import os
import csv

def str_to_sec(time_str):
    h, m, s = time_str.replace("_", ":").split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def str_to_mins(time_str):
    return math.ceil(str_to_sec(time_str) / 60)

def check_saving_path(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def get_system_name():
    return platform.uname().system

def sec_to_str(sec):
    seconds = int(sec)
    microseconds = (sec * 1000000) % 1000000
    td = datetime.timedelta(0, seconds, microseconds)
    total_seconds = td.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    output = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    return output

def get_my_ip_address():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
        sock.close()
        return ip_address
    except socket.error:
        return None
        
def get_role():
    return get_from_config('device_type')
                
def get_target_ip():
    return get_from_config('target_device_ip')
                
def get_communication_port():
    return get_from_config('communication_port')
            
def get_from_config(key):
    with open(os.path.join("data", 'device_config.csv'), 'r') as file:
        reader = csv.reader(file, delimiter=',', quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
        for row in reader:
            if row[0] == key:
                return row[1]