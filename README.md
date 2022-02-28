# What is adsb_radius_alert
Send alerts based on if aircraft are withing a certain range of a point based on data gathered by fa-dump1090

# To Do still
- Regex of aircraft name per point
 - code added but is untested
- System to not alert multiple times on an aircraft

# Python packages needed
```
pip3 install apprise
pip3 install geopy
```

# Running it
First edit the variables at the top to suit your needs.  Then simply call the script at an interval
```
python3 alert_check.py
```
