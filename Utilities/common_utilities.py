from pathlib import Path
import platform
import datetime
import math

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