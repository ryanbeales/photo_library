from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
from datetime import datetime



class Location(object):
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
    
    def __str__(self):
        return f'{self.lat},{self.lng}'

class Locations:
    """
    {
        "locations" : [ {
            "timestampMs" : "1265928103110", # Epoch in ms.
            "latitudeE7" : -380005980, # Divide by 1e7
            "longitudeE7" : 1452375430, # Divide by 1e7
            "accuracy" : 1046
        }, {
            "timestampMs" : "1265928486819",
            "latitudeE7" : -380005980,
            "longitudeE7" : 1452375430,
            "accuracy" : 1046
        },
    """
    def __init__(self, history_file='Location_History.json', enable_geopy=False):
        with open(history_file) as f:
            locations=json.load(f)
        
        self.locations = {}
        for l in locations['locations']:
            timestamp = datetime.fromtimestamp(int(l['timestampMs']) / 1000.0)
            lat = l['latitudeE7'] / 1e7
            lng = l['longitudeE7'] / 1e7
            self.locations[timestamp] = [lat, lng]
        
        self.location_keys = sorted(self.locations.keys())
        self.enable_geopy = enable_geopy
        if self.enable_geopy:
            self.geolocator = Nominatim(user_agent="RB PhotoGeoCoder")
            self.reverse = RateLimiter(self.geolocator.reverse, min_delay_seconds=2)


    def get_location_at_timestamp(self, timestamp):
        # Search for minimum difference in list of keys
        closest_timestamp = min(self.location_keys, key=lambda d: abs(d-timestamp))
        # if self.enable_geopy, do stuff...
        return self.locations[closest_timestamp]