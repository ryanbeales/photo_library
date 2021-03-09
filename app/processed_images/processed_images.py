import json
from dataclasses import dataclass
import datetime
import os
from sqlalchemy import create_engine

from threading import Thread, Lock
from queue import Queue, Empty

import logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessedImage():
    filetype: str
    filename: str
    date_taken: datetime.datetime
    exif_data: dict
    thumbnail: str
    latitude: float
    longitude: float


class ProcessedImages(object):
    def __init__(self, db_dir=None):
        self.db_file = db_dir + os.sep + 'images.db'
        
    def load(self):
        logger.info(f'Opening photo database {self.db_file}')

        #self.conn = sqlite3.connect(self.db_file, check_same_thread=False, isolation_level=None)
        self.conn = create_engine('sqlite:///' + self.db_file)

        logger.debug('Create table if not exists')
        c = self.conn
        c.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                filename TEXT NOT NULL PRIMARY KEY,
                filetype TEXT NOT NULL,
                date_taken INTEGER,
                exif_data TEXT,
                thumbnail TEXT,
                latitude REAL,
                longitude REAL
            );
        ''')

        c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS photos_filename_ids on photos(filename);''')
        c.execute('''PRAGMA foreign_keys = ON;''')
        c.execute('''PRAGMA journal_mode = MEMORY;''')

    def add(self, metadata):
        insert_values = (
            metadata.filename,
            metadata.filetype,
            int(metadata.date_taken.timestamp()),
            json.dumps(metadata.exif_data),
            metadata.thumbnail,
        )
        logger.debug(f'INSERT or REPLACE row for {metadata.filename}')
        try:
            c = self.conn #.cursor()
            c.execute('''
                REPLACE INTO 
                photos (filename, filetype, date_taken, exif_data, thumbnail) 
                VALUES (?,?,?,?,?)  
            ''', insert_values)
            #self.conn.commit()
            #c.close()
        except Exception as e:
                logger.error(f'Failed to insert {metadata.filename}: {e}')

    def create_hdr_set(self, filenames):
        name = '-'.join([os.path.basename(i.filename) for i in filenames])
        inserts = [(name, i.filename) for i in filenames]
        logger.debug(f'creating hdr set {name} = {inserts}')
        for insert in inserts:
            c = self.conn
            c.execute('''
                REPLACE INTO hdr_groups VALUES (?,?)
            ''', insert)
            self.conn.commit()
            c.close()

    def check_if_processed(self, filename):
        logger.debug(f'Checking if {filename} already exists in DB')
        
        c = self.conn
        rs = c.execute('''
            SELECT EXISTS(SELECT 1 FROM photos WHERE filename=?)
        ''', ( filename, ))
        r = rs.fetchone()

        if r[0] == 1:
            logger.warning(f'Already exists {filename}')
            return True
        else:
            return False

    def get_file_list(self):
        logger.debug(f'Get list of all filenames ordered by date taken')
        c = self.conn
        rs = c.execute('''
            SELECT filename FROM photos ORDER BY filename, date_taken
        ''')
        r = rs.fetchall()
        results = [x[0] for x in r]
        return results

    def get_raw_files(self):
        logger.debug(f'Get list of all filenames ordered by date taken')
        c = self.conn
        rs = c.execute('''
            SELECT filename FROM photos WHERE filetype = 'RAW' ORDER BY filename, date_taken
        ''')
        r = rs.fetchall()
        results = [x[0] for x in r]
        return results

    def get_empty_locations(self):
        logger.debug(f'Get list of all filenames that do not have any location data')
        c = self.conn
        rs = c.execute('''
            SELECT filename, date_taken FROM photos WHERE latitude IS NULL and longitude IS NULL ORDER BY filename, date_taken
        ''')
        r = rs.fetchall()
        results = [x[0] for x in r]
        return results

    def set_location(self, filename, lat, lng):
        logger.debug(f'Adding coords for {filename}')
        c = self.conn
        c.execute('''
            UPDATE photos SET (latitude = ?, longitude = ?) WHERE filename = ?
        ''', (lat, lng, filename, ))
        #c.close()

    def retrieve(self, filename):
        logger.debug(f'Retreive data for {filename}')
        c = self.conn
        rs = c.execute('''
            SELECT filename, filetype, date_taken, exif_data, thumbnail, latitude, longitude
            FROM photos
            WHERE filename = ?
        ''', ( filename, ))
        r = rs.fetchone()
        if r == None:
            return None

        exif_data = json.loads(r[3]) if r[3] else dict()

        p = ProcessedImage(
            filename = r[0],
            filetype = r[1],
            date_taken = datetime.datetime.fromtimestamp(r[2]),
            exif_data = exif_data,
            thumbnail = r[4],
            latitude = r[5],
            longitude = r[6]
        )
        return p
    
    def commit(self):
        logger.debug('commit called, doing nothing')
        pass
    
    def close(self):
        logger.debug('closing database')
        self.conn.close()


class QueueingProcessedImages():
    def __init__(self, db_dir=None):
        logger.debug('Created processed images queue')
        self.lock = Lock()
        self.p = ProcessedImages(db_dir=db_dir)
        self.add_queue = Queue()

    def start(self):
        logger.debug('Starting processed images queue')
        self.p.load()
        self.add_thread = Thread(target=self.process_add_queue)
        self.add_thread.start()

    def stop(self):
        # Signal to threads that we want them to stop
        logger.debug('Sending None to queues to stop')
        self.add_queue.put(None)

        # Wait for the queue processing to finish, which happens when the above is picked up
        logger.debug('Waiting for queues to finish processing')
        self.add_queue.join()

        # Wait for threads to exit and join
        logger.debug('Waiting for threads to finish')
        self.add_thread.join()
        logger.debug('Stopped processed images queue')

        logger.debug('Stopping processed images queue')
        logger.debug('Sending commit')
        self.p.commit()
        self.p.close()


    def process_add_queue(self):
        locked = False
        while True:
            item = self.add_queue.get()
            if item is None:
                self.add_queue.task_done()
                logger.debug('add queue recieved shutdown signal')
                break
            
            if not locked:
                locked = self.lock.acquire()

                logger.debug(f'retrieved item from add queue, {self.add_queue.qsize()} items remaining')
                self.p.add(item)
            self.add_queue.task_done()

            # Release lock when queue is empty.
            if self.add_queue.qsize() < 1:
                self.lock.release()
                locked = False

    def add(self, metadata):
        # Place data in a queue, and return immediately
        self.add_queue.put(metadata)

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