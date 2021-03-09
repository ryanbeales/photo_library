import os
from ingest.image import Image

from processed_images.processed_images import LockingProcessedImages, ProcessedImages, QueueingProcessedImages, ProcessedImage

from threading import Lock
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

import logging
logger = logging.getLogger(__name__)


class DirectoryWorker(object):
    def __init__(
        self,
        #classifer=None,  #Classifier('/work/nasnet/nasnet_large.tflite', '/work/nasnet/labels.txt'),
        #object_detector=None, #ObjectDetector('/work/object_detector'),
        processed_images=LockingProcessedImages(db_dir='/work/stash/src/classification_output/'),
        file_types=['.CR2', '.CR3', '.JPG']
    ):
        self.processed_images = processed_images
        self.file_types = file_types
        self.found_files = []
    
    def get_image_files(self, base_dir, file_types=None):
        logger.debug(f'finding files in {base_dir}')
        if not file_types:
            file_types = self.file_types

        previous_count = self.get_total_files()
        for root, _, files in os.walk(base_dir, topdown = False):
            for name in files:
                fullpath = os.path.join(root, name)
                if os.path.splitext(fullpath)[-1].upper() in file_types:
                    self.found_files.append(fullpath)
        logger.info(f'found {len(self.found_files)-previous_count} in {base_dir}')
        return self.found_files

    def set_directory(self, directory):
        self.get_image_files(directory)

    def get_total_files(self):
        return len(self.found_files)

    def dummy_callback(self, image_file, state):
        logger.debug(f'dummy callback: {image_file}, {state}')

    def stop(self):
        logger.debug('stop worker')
        self.processed_images.stop()

    def scan(self, reprocess=False, processed_file_callback=None):
        logger.info('Starting scan')
        self.processed_images.start()
        if not processed_file_callback:
            processed_file_callback = self.dummy_callback

        logger.info('Creating thread pool executor')
        with ThreadPoolExecutor() as executor:
            results = [
                executor.submit(
                    self.process_single_image_thread,
                    image_file=image_file, 
                    reprocess=reprocess, 
                    processed_file_callback=processed_file_callback
                )
                for image_file in self.found_files
            ]
            # I need to check for bad results in all of these:
            logger.info('Waiting for all threads to finish')
            wait(results, return_when=ALL_COMPLETED)

            # If we don't do this the tread might result in an exception which is never shown.
            # But looking at each result we cause the Exception to be displayed at least.
            for result in results:
                if result.result():
                    logger.debug(f'Thread result: {result.result()}')

        processed_file_callback('All', 'done')
        self.processed_images.stop()
        logger.info('Finished scan')

    def process_single_image_thread(self, image_file, reprocess, processed_file_callback):
        processed_file_callback(image_file, 'start')

        if self.processed_images.check_if_processed(image_file) and not reprocess:
            logger.debug(f'already processed {image_file}')
            processed_file_callback(image_file, 'already_processed')
            return

        logger.info(f'Processing {image_file}')
        try:
            image = Image(image_file)
        except Exception as e:
            logger.error(f'Exception during image processing {e}')
            processed_file_callback(image_file, 'error')
            return None    

        metadata = ProcessedImage(
            filename=image_file,
            filetype=image.filetype,
            date_taken=image.get_photo_date(),
            exif_data = image.get_json_safe_exif(),
            thumbnail=image.get_thumbnail(),
            latitude=None,
            longitude=None
        )

        logger.info(f'Sending {image_file} metadata to processed images')
        self.processed_images.add(metadata)

        processed_file_callback(image_file, 'end')


class MultiDirectoryWorker(DirectoryWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_directory(self, directories):
        if type(directories) == list:
            for directory in directories:
                super().set_directory(directory)
        else:
            super().set_directory(directories)
