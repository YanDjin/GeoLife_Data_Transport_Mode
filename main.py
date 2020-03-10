import re
import requests
import datetime
from xml.etree import ElementTree
from math import sin, cos, sqrt, atan2, radians

def open_trajectory():
    lat1 = 0
    lon1 = 0
    R = 6373.0
    trajectory = open("Geolife/Data/000/Trajectory/20081023025304.plt", "r")
    for x in range(6):
        trajectory.readline()
    lines = trajectory.readlines()
    for i, line in enumerate(lines):
        data = line.split(',')
        lat2 = radians(float(data[0]))
        lon2 = radians(float(data[1]))
        date = data[5]
        time2 = data[6]

        if lat1 is 0 or lon1 is 0:
            lat1 = lat2
            lon1 = lon2
            time1 = time2
        else:
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = R * c

            print(str(i) + " Result:", round(distance*1000), "m")
            lat1 = lat2
            lon1 = lon2


def getStreetName(lat, lon):
    response = requests.get("http://nominatim.openstreetmap.org/reverse?format=xml&lat="+lat+"&lon="+lon+"&zoom=18&addressdetails=1")
    tree = ElementTree.fromstring(response.content)
    return tree[1][0].text + " " + tree[1][1].text


open_trajectory()
