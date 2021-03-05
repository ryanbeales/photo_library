from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
from datetime import datetime
import sqlite3
import os

from threading import Lock

import logging
logger = logging.getLogger(__name__)


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
    def __init__(self, history_file=None, history_db_dir=None, enable_geopy=False):
        self.location_database_name = history_db_dir + os.sep + 'locations.db'

        self.conn = sqlite3.connect(self.location_database_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = Lock()

        if not self.check_database_current(history_file):
            self.load_json_data(history_file)

        self.enable_geopy = enable_geopy
        if self.enable_geopy:
            self.geolocator = Nominatim(user_agent="RB PhotoGeoCoder")
            self.reverse = RateLimiter(self.geolocator.reverse, min_delay_seconds=2)

    def __del__(self):
        self.conn.close()

    def create_tables(self):
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS locations (
                timestamp INTEGER,
                lat INTEGER,
                lng INTEGER, 
                accuracy INTEGER
            );
            CREATE TABLE IF NOT EXISTS historytimestamp (
                timestamp INTEGER
            );
            CREATE INDEX IF NOT EXISTS locations_idx ON locations ( timestamp );
        ''')

    def check_database_current(self, filename):
        self.cursor.execute('SELECT timestamp from historytimestamp;')
        r = self.cursor.fetchone()

        if r and r[0] == int(os.stat(filename).st_ctime):
            return True
        return False

    def load_json_data(self, jsonfile):
        # Get a lock if we're loading everything in
        with self.lock:
            self.create_tables()
            self.cursor.execute('DELETE FROM locations')
            self.cursor.execute('DELETE FROM historytimestamp')
            self.cursor.execute('INSERT INTO historytimestamp VALUES (?)', (int(os.stat(jsonfile).st_ctime), ))

            with open(jsonfile) as f:
                locations=json.load(f)

            for l in locations['locations']:
                timestamp = int(l['timestampMs']) / 1000
                lat = l['latitudeE7']
                lng = l['longitudeE7']
                accuracy = l['accuracy'] if 'accuracy' in l else -1

                self.cursor.execute('INSERT INTO locations VALUES(?, ?, ?, ?);', (timestamp, lat, lng, accuracy))
            self.conn.commit()

    def get_location_at_timestamp(self, timestamp):
        # Convert incoming datetime object to a timestamp int
        t = int(timestamp.timestamp())

        # Acquire a lock before running the below
        with self.lock:
            # Find the two nearest values to the timestamp given, and return the lat/lng associated with both
            self.cursor.execute('''
                SELECT lat,lng FROM locations WHERE timestamp IN (
                    SELECT MIN(timestamp) FROM locations where timestamp >= ?
                    UNION
                    SELECT MAX(timestamp) from locations where timestamp <= ?
                )
            ''', (t, t, ) )

            r = self.cursor.fetchall()

            # Release the lock now we're done executing.

        # If there's more than one result, average the two
        if len(r) > 1:
            lat1= r[0][0]
            lng1= r[0][1]

            lat2= r[1][0]
            lng2= r[1][1]

            # Average both, and convert to usual lat/lng number format
            lat = ((lat1+lat2) / 2) / 1e7
            lng = ((lng1+lng2) / 2) / 1e7
        else:
            # Just one result, convert to usual lat/lng number format
            lat = r[0][0] / 1e7
            lng = r[0][1] / 1e7

        return [lat,lng]

if __name__ == '__main__':
    locations=Locations(history_file=r'S:\Backup\Google Location History\Location History.json', history_db_dir=r'S:\src\classification_output')
