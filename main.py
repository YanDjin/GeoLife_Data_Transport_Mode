import re
import requests
from datetime import datetime
from xml.etree import ElementTree
from math import sin, cos, sqrt, atan2, radians

def open_trajectory():
    lat1 = 0
    lon1 = 0
    time1 = ""
    try:
        trajectory = open("Geolife/Data/056/Trajectory/20071017150317.plt", "r")
        for x in range(6):
            trajectory.readline()
        lines = trajectory.readlines()
        for i, line in enumerate(lines):
            data = line.split(',')
            lat = data[0]
            lon = data[1]
            lat2 = radians(float(data[0]))
            lon2 = radians(float(data[1]))
            date = data[5]
            time2 = data[5] + " " + data[6]

            if lat1 is 0 or lon1 is 0:
                lat1 = lat2
                lon1 = lon2
                time1 = time2
            else:
                distance = get_travel_distance(lat1, lat2, lon1, lon2)
                get_velocity(time1, time2, distance)
                #print(get_street_name(lat, lon))

                lat1 = lat2
                lon1 = lon2
                time1 = time2
    except FileNotFoundError:
        print("File not found")


def get_street_name(lat, lon):
    response = requests.get("http://nominatim.openstreetmap.org/reverse?format=xml&lat="+lat+"&lon="+lon+"&zoom=18&addressdetails=1")
    tree = ElementTree.fromstring(response.content)
    return tree[1][0].text + " " + tree[1][1].text


def get_velocity(time1, time2, distance):
    timestamp1 = datetime.timestamp(datetime.strptime(time1, "%Y-%m-%d %H:%M:%S\n"))
    timestamp2 = datetime.timestamp(datetime.strptime(time2, "%Y-%m-%d %H:%M:%S\n"))
    velocity = distance / (timestamp2 - timestamp1) * 3600
    print(str(round(velocity)) + "km/h")


def get_travel_distance(lat1, lat2, lon1, lon2):
    R = 6373.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    print("Result:", round(distance * 1000), "m")
    return distance

open_trajectory()
