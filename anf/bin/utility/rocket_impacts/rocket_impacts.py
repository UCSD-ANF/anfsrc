#!/usr/bin/env python

# This will print some instructions that you
# can input in this tool to plot the data:
#   https://www.freemaptools.com/concentric-circles.htm

import json

print("Locate Rocket impact sites: \n")
print("Copy/Paste the text to this website:")
print("\thttps://www.freemaptools.com/concentric-circles.htm\n")


sites = json.load(open("rocket_impacts_sites.conf"))

# plot sites
for sta in sites:
    print(
        '"%f,%f",0,3,%s' % (sites[sta]["lat"], sites[sta]["lon"], sites[sta]["color"])
    )

# plot known points
points = json.load(open("rocket_impacts_points.conf"))
for point in points:
    print('"%f,%f",0,%d,%s' % (point[0], point[1], point[2], point[3]))

# plot circles
times = [90, 105]
speed = 320
m2km = 1000
km2d = 110
m2d = 111000
d2r = 0.0174533


# plot circles
delay = json.load(open("rocket_impacts_delays.conf"))

for k in delay:

    if k in sites:
        lat = sites[k]["lat"]
        lon = sites[k]["lon"]
        time_delay = delay[k]["delay"]

        start = ((times[0] + time_delay) * speed) / m2km
        end = ((times[1] + time_delay) * speed) / m2km

        print(
            '"%f,%f",%f,%f,%s'
            % (sites[k]["lat"], sites[k]["lon"], start, end, sites[k]["color"])
        )

    else:
        print("SITE %s NOT IN CONFIG FILE" % k)
