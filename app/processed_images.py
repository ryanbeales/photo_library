import json
from dataclasses import dataclass
import datetime
import os
import sqlite3

@dataclass
class ProcessedImage():
    filename: str
    classification: dict
    detected_objects: dict
    location: list
    date_taken: datetime.datetime
    exif_data: dict
    bracket_shot_count: int
    bracket_mode: int
    bracket_exposure_value: int
    thumbnail: str


class ProcessedImages(object):
    def __init__(self, db_dir=None):
        self.db_file = db_dir + os.sep + 'images.db'

        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

        self.load()
        
    def __del__(self):
        self.conn.close()

    def load(self):
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS photos (
                filename TEXT NOT NULL PRIMARY KEY,
                classification TEXT,
                detected_objects TEXT,
                latitude REAL,
                longitude REAL,
                date_taken INTEGER,
                exif_data TEXT,
                thumbnail TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS photos_filename_ids on photos(filename);
            
            PRAGMA foreign_keys = ON;
            
            CREATE TABLE IF NOT EXISTS hdr_groups (
                name TEXT NOT NULL PRIMARY KEY,
                filename TEXT,
                FOREIGN KEY(filename) REFERENCES photos(filename)
            );
        ''')

    def add(self, metadata):
        insert_values = (
            metadata.filename,
            json.dumps(metadata.classification),
            json.dumps(metadata.detected_objects),
            metadata.location[0],
            metadata.location[1],
            int(metadata.date_taken.timestamp()),
            json.dumps(metadata.exif_data),
            metadata.thumbnail
        )
        self.cursor.execute('''
            REPLACE INTO photos VALUES (?,?,?,?,?,?,?,?)  
        ''', insert_values)

    def create_hdr_set(self, filenames):
        name = '-'.join([os.path.basename(i.filename) for i in filenames])
        inserts = [(name, i.filename) for i in filenames]
        print(f'creating hdr set {name} = {inserts}')
        for insert in inserts:
            self.cursor.execute('''
                REPLACE INTO hdr_groups VALUES (?,?)
            ''', insert)

    def retrieve(self, filename):
        self.cursor.execute('''
            SELECT filename, classification, detected_objects, latitude, longitude, date_taken, exif_data, thumbnail
            FROM photos
            WHERE filename = ?
        ''', ( filename, ))
        r = self.cursor.fetchone()

        if r == None:
            return None

        classification = json.loads(r[1]) if r[1] else dict()
        detected_objects = json.loads(r[2]) if r[2] else dict()
        exif_data = json.loads(r[6]) if r[6] else dict()

        p = ProcessedImage(
            filename = r[0],
            classification = classification,
            detected_objects = detected_objects,
            location = [r[3],r[4]],
            date_taken = datetime.datetime.fromtimestamp(r[5]),
            exif_data = exif_data,
            thumbnail = r[7],
            bracket_exposure_value=0,
            bracket_mode=0,
            bracket_shot_count=0
        )
        return p
    
    def commit(self):
        self.conn.commit()