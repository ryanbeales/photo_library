import json
from dataclasses import dataclass
import datetime
import os
import sqlite3

from threading import Thread, Lock
from queue import Queue, Empty

import logging
logger = logging.getLogger(__name__)


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

        logger.info(f'Opening photo database {self.db_file}')
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.load()
        
    def __del__(self):
        self.conn.close()

    def load(self):
        logger.debug('Create table if not exists')
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS photos (
                filename TEXT NOT NULL PRIMARY KEY,
                classification TEXT,
                detected_objects TEXT,
                latitude REAL,
                longitude REAL,
                date_taken INTEGER,
                exif_data TEXT,
                thumbnail TEXT,
                bracket_exposure_value INTEGER,
                bracket_mode INTEGER,
                bracket_shot_count INTEGER
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
            metadata.thumbnail,
            metadata.bracket_exposure_value,
            metadata.bracket_mode,
            metadata.bracket_shot_count
        )
        logger.debug(f'INSERT or REPLACE row for {metadata.filename}')
        self.cursor.execute('''
            REPLACE INTO photos VALUES (?,?,?,?,?,?,?,?,?,?,?)  
        ''', insert_values)

    def create_hdr_set(self, filenames):
        name = '-'.join([os.path.basename(i.filename) for i in filenames])
        inserts = [(name, i.filename) for i in filenames]
        logger.debug(f'creating hdr set {name} = {inserts}')
        for insert in inserts:
            self.cursor.execute('''
                REPLACE INTO hdr_groups VALUES (?,?)
            ''', insert)

    def check_if_processed(self, filename):
        logger.debug(f'Checking if {filename} already exists in DB')
        self.cursor.execute('''
            SELECT EXISTS(SELECT 1 FROM photos WHERE filename=?)
        ''', ( filename, ))
        r = self.cursor.fetchone()
        if r[0] == 1:
            return True
        else:
            return False

    def get_file_list(self):
        logger.debug(f'Get list of all filenames ordered by date taken')
        self.cursor.execute('''
            SELECT filename FROM photos ORDER_BY filename, date_taken
        ''')
        r = self.cursor.fetchall()
        results = [x[0] for x in r]
        return results

    def retrieve(self, filename):
        logger.debug(f'Retreive data for {filename}')
        self.cursor.execute('''
            SELECT filename, classification, detected_objects, latitude, longitude, date_taken, exif_data, thumbnail, bracket_exposure_value, bracket_mode, bracket_shot_count
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
            bracket_exposure_value=r[8],
            bracket_mode=r[9],
            bracket_shot_count=r[10]
        )
        return p
    
    def commit(self):
        logger.debug('commit called')
        try:
            self.conn.commit()
        except:
            logger.error('commit failed')
            pass


class QueueingProcessedImages():
    def __init__(self, db_dir=None):
        logger.debug('Created processed images queue')
        self.lock = Lock()
        self.p = ProcessedImages(db_dir=db_dir)
        self.add_queue = Queue()
        self.hdr_queue = Queue()

    def start(self):
        logger.debug('Starting processed images queue')
        self.add_thread = Thread(target=self.process_add_queue)
        self.hdr_thread = Thread(target=self.process_hdr_queue)
        self.add_thread.start()
        self.hdr_thread.start()

    def stop(self):
        # This is working...
        logger.debug('Stopping processed images queue')
        logger.debug('Sending commit')
        self.p.commit()

        # Signal to threads that we want them to stop
        logger.debug('Sending None to queues to stop')
        self.add_queue.put(None)
        self.hdr_queue.put(None)

        # Wait for the queue processing to finish, which happens when the above is picked up
        logger.debug('Waiting for queues to finish processing')
        self.add_queue.join()
        self.hdr_queue.join()

        # Wait for threads to exit and join
        logger.debug('Waiting for threads to finish')
        self.add_thread.join()
        self.hdr_thread.join()
        logger.debug('Stopped processed images queue')    

    def process_add_queue(self):
        while True:
            item = self.add_queue.get()
            if item is None:
                self.add_queue.task_done()
                logger.debug('add queue recieved shutdown signal')
                break
            with self.lock:
                logger.debug(f'retrieved item from add queue, {self.add_queue.qsize()} items remaining')
                self.p.add(item)
                self.p.commit()
            self.add_queue.task_done()

    def process_hdr_queue(self):
        while True:
            item = self.hdr_queue.get()
            if item is None:
                self.hdr_queue.task_done()
                logger.debug('hdr queue recieved shutdown signal')
                break
            with self.lock:
                logger.debug(f'retrieved item from hdr queue, {self.hdr_queue.qsize()} items remaining')
                self.p.create_hdr_set(item)
            self.hdr_queue.task_done()

    def add(self, metadata):
        # Place data in a queue, and return immediately
        self.add_queue.put(metadata)
    
    def create_hdr_set(self, filenames):
        # Place data in a queue and return immediately
        self.hdr_queue.put(filenames)

    def commit(self):
        # This should do nothing in the queueing version.
        pass

    def get_file_list(self):
        with self.lock:
            return self.p.get_file_list()

    def retrieve(self, filename):
        # Blocking, until we can get the connection
        with self.lock:
            return self.p.retrieve(filename)
    
    def check_if_processed(self, filename):
        # Blocking, until we can get the connection
        with self.lock:
            return self.p.check_if_processed(filename)