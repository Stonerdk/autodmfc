from datetime import datetime
from constants import DENSITY, MATTER_PRICE

def calculate_price(value):
    return value / 1000 / DENSITY * MATTER_PRICE

def calculate_kg(value):
    return value / 1000 / DENSITY

def pairwise(iterable):
    iterator = iter(iterable)
    prev = next(iterator, None)
    for item in iterator:
        yield prev, item
        prev = item

def hms2sec(hms_string):
    time_obj = datetime.strptime(hms_string, "%H:%M:%S")
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_seconds

def strftoday(format = "%Y%m%d"):
    return datetime.now().strftime(format)