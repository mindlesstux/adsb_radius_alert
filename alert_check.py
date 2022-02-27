# ==========================================================================
#   Variables that need to be reviewed and set
# ==========================================================================

# URL of flightaware aircraft.json
aircraft_json_url = "https://mindlesstux.com/skyaware/data/aircraft.json"

# Dictionary of points to alrt around
# "pointname": [lat, long, altitude low, altitude high, radius/km, point text friendly name, regex flight]
alert_cords = {
    "KRDU": [35.879204, -78.787162, 0, 1000000, 30, "RDU Airport", ()],
    "Point_2": [0, 0, 0, 1000000, 30, "Far Point", ()],
}

# At the end output to console some json
print_json_output = True

# Skip notifiying services
send_apprise = True

# Outer dictionary name must match the alert_cords dictionary name
alert_apprise = {
    'KRDU': {
        "targets": ["discord://webhook_id/webhook_token"],
        "title": "Aircraft Alert",
        "message": "Aircraft $hex ($flight) is near by!  It is $distance km away at $altitude ft"
    }
}

# Turn on debug logging
debug_logs = True
debug_more = True

# ==========================================================================
#   Dont touch the code below
# ==========================================================================

# Import the various libraries we will need
import apprise
from geopy import distance
import json
from string import Template
import time
from urllib.request import urlopen

alerts = {}

# This is to be kind of a caching buster
aircraft_json_url += "?_"
aircraft_json_url += str(int(time.time()))

# Debug output of the URL
if debug_logs:
    print("Generated URL: %s" % (aircraft_json_url))

# Use GeoPy to do the math for us into kilometers
def check_within_radius(coords_center, coords_target, radius_limit):
    target_distance = distance.distance(coords_center, coords_target).km
    target_distance = round(target_distance,3)
    if radius_limit >= target_distance:
        return (True, target_distance)
    else:
        return (False, target_distance)

def check_altitude_limits(alt_low, alt_high, target_alt):
    if alt_high > target_alt > alt_low:
        return (True, target_alt)
    else:
        return (False, 0)

# Pull down the aircraft.json file and load it to an variable
response = urlopen(aircraft_json_url)
aircraft_data = json.loads(response.read())

# Debug output of the data array
if debug_logs:
    print("Loaded aircraft data")
if debug_more:
    print(json.dumps(aircraft_data, indent=4, sort_keys=True))

# Loop through all the aircraft
for name, point in alert_cords.items():
    if debug_logs:
        print(name)
        print("[lat, long, alt_low, alt_high, radius (km), friendly name")
        print(point)
    # Data for each point alerting around
    coords_center = (point[0], point[1])
    altitude_limit_low = point[2]
    altitude_limit_high = point[3]
    radius_limit = point[4]
    friendly_name = point[5]

    # Loop through all aircraft
    tmp={}
    for aircraft in aircraft_data['aircraft']:
        # Do we have lat/long for the aircraft? If not asusme its out of the area we care about
        if "lat" in aircraft.keys() and "lon" in aircraft.keys():
            coords_target = (aircraft['lat'], aircraft['lon'])
            result_radius = check_within_radius(coords_center, coords_target, radius_limit)
        else:
            result_radius = [False, 0]
        
        # Do we have barometric altitude? If not just assume its true for simplicity
        if "alt_baro" in aircraft.keys():
            result_altitude = check_altitude_limits(altitude_limit_low, altitude_limit_high, aircraft['alt_baro'])
        else:
            result_altitude = [True, 0]

        # Is the plane in the point radius for alerting?
        if result_radius[0] == True and result_altitude[0] == True:
            # Add a blank flight info if it does not exist
            if "flight" not in aircraft.keys():
                aircraft['flight'] = "        "

            # Build a dictionary to add to existing
            tmp2 = {aircraft['hex']: {'distance': result_radius[1], 'altitude': result_altitude[1], 'flight': aircraft['flight']}}
            tmp.update(tmp2)
            
    # If something was added to tmp as an alert build out the alerts dictionary
    if tmp:
        alerts[name] = {}
        alerts[name]['friendly_name'] = friendly_name
        alerts[name]['alt_low'] = altitude_limit_low
        alerts[name]['alt_high'] = altitude_limit_high
        alerts[name]['radius_limit'] = radius_limit
        alerts[name]['coord_center'] = coords_center
        alerts[name]['aircraft'] = {}
        alerts[name]['aircraft'].update(tmp)


# Create an Apprise instance
if send_apprise:
    if debug_logs:
        print()
        print("Defined alert targets for points")
    for x,y in alert_apprise.items():
        if debug_logs:
            print("    Alerting for point: %s" % x)
            print("    Stuff: %s" % y)
            print()
        apobj = apprise.Apprise()
        for tgts in y['targets']:
            if debug_logs:
                print("Addings: %s for %s" % (tgts, x))
            apobj.add(tgts)
        
        if debug_logs:
            print()

        for a,b in alerts.items():
            if x == a:
                for asdf, fdsa in b['aircraft'].items():
                    if debug_more:
                        print("Aircraft hex: %s" % asdf)
                        print("Aircraft details: %s" % fdsa)
                    temp_title_obj = Template(y['title'])
                    formated_title = temp_title_obj.substitute(hex=asdf, flight=fdsa['flight'], distance=fdsa['distance'], altitude=fdsa['altitude'])
                    temp_msg_obj = Template(y['message'])
                    formated_message = temp_msg_obj.substitute(hex=asdf, flight=fdsa['flight'], distance=fdsa['distance'], altitude=fdsa['altitude'])
                    if debug_logs:
                        print("Title: %s" % formated_title)
                        print("  Msg: %s" % formated_message)
                        print()

        del apobj
    
if print_json_output:
    print()
    print(json.dumps(alerts))
