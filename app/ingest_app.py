# Example https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py

from config import config

import logging
logging.getLogger('PIL.TiffImagePlugin').setLevel(logging.ERROR)

import time
from datetime import timedelta
from pprint import pprint

from ingest.workers import MultiDirectoryWorker

import os

from progress.bar import Bar

from threading import Lock

class Display():
    def __init__(self, total_images, progress_bar=True):
        self.count = 0
        self.total_images = total_images
        self.average_image_time = 1
        self.lock = Lock()

        if progress_bar:
            self.progress = Bar('Processing images', width=110, max=total_images, suffix='%(index)d/%(max)d - %(eta)ds')


    def display_callback(self, image_file, state):
        # Make this add to a queue, then separate the display out in to it's own thread
        with self.lock:
            if state == 'start':
                self.start_time = time.time()
                self.count = self.count + 1
            elif state == 'already_processed':
                if self.progress:
                    self.progress.next()
                else:
                    print(f'Already processed {image_file} previously, skipping')
            elif state == 'end':
                self.end_time = time.time()
                self.average_image_time = (self.average_image_time + (self.end_time - self.start_time)) / 2
                images_left = self.total_images - self.count
                time_left = timedelta(seconds=self.average_image_time * images_left)
        
                if self.progress:
                    self.progress.next()
                else:
                    print(f"Finished processing {image_file}")
                    print("Time on image: ", self.end_time-self.start_time)
                    print(f"Approximate time left: {time_left}")
            elif state == 'done':
                self.progress.finish()
                # Monitor queue size?
                print('waiting for queue to empty...')

if __name__ == '__main__':
    logging.basicConfig(
        filename=config['logging']['log_file'], 
        filemode='w', 
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=config['logging']['log_level']
    )
    logger = logging.getLogger(__name__)

    logger.debug('Creating worker object')
    w = MultiDirectoryWorker()

    # Get list of paths from section in config file, but exclude default keys (including the base path...)
    paths = [ v for k,v in config['ingest_paths'].items() if k not in config['DEFAULT'].keys()]
    logging.debug(f'Setting paths to process: {paths}')
    print('Scanning directories for files...')
    w.set_directory(paths)

    total_files = w.get_total_files()
    logging.info(f'total files to process {total_files}')

    logging.debug('creating display object')
    d = Display(total_files, progress_bar=config['ingest'].getboolean('progress_bar'))
    reprocess = config['ingest'].getboolean('reingest')

    logging.info(f'reprocessing of files set to {reprocess}')
    logging.debug('starting scan of paths')
    w.scan(reprocess=reprocess, processed_file_callback=d.display_callback)
    logging.debug('finished scanning all files')
    print('')

    #print('Generating map')
    #w.make_map('/work/stash/src/classification_output/image_map.html')
    #print('Done!')