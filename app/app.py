# Example https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py

import logging

import time
from datetime import timedelta
from pprint import pprint
from workers import MultiDirectoryWorker

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

paths = [
    # Selection of all cameras that produce RAW files:
    r'/work/stash/Photos/Canon EOS M5/2018/12/22',
    r'/work/stash/Photos/60D/2012/05',
    r'/work/stash/Photos/350D/2012/01/07',
    r'/work/stash/Photos/Canon EOS M6 II/2019/12/02/CR3',
    r'/work/stash/Photos/M3/2017/04/08/CR2',
]

if __name__ == '__main__':
    logging.basicConfig(
        filename=r'/work/stash/src/classification_output/images.log', 
        filemode='w', 
        encoding='utf-8',
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        level=logging.DEBUG
    )
    logger = logging.getLogger(__name__)

    logger.info
    w = MultiDirectoryWorker(classifer=None, object_detector=None)

    w.set_directory(paths)
    total_files = w.get_total_files()
    d = Display(total_files, progress_bar=True)
    reprocess = False
    if 'PHOTO_REPROCESS' in os.environ:
        reprocess=True
    w.scan(reprocess=reprocess, processed_file_callback=d.display_callback)
    print('')
    #print('Generating map')
    #w.make_map('/work/stash/src/classification_output/image_map.html')
    #print('Done!')