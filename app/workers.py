import os
from image import Image
#from classifier import Classifier
#from objectdetector import ObjectDetector
from locations import Locations
from hdr_finder import HDRFinder
from map_maker import MapMaker
from processed_images import QueueingProcessedImages, ProcessedImage

from threading import Lock
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


class DirectoryWorker(object):
    def __init__(
        self,
        classifer=None,  #Classifier('/work/nasnet/nasnet_large.tflite', '/work/nasnet/labels.txt'),
        object_detector=None, #ObjectDetector('/work/object_detector'),
        locations=Locations(history_file=r'/work/stash/Backup/Google Location History/Location History.json', history_db_dir='/work/stash/src/classification_output/'),
        processed_images=QueueingProcessedImages(db_dir='/work/stash/src/classification_output/'),
        file_types=['.CR2', '.CR3', '.JPG']
    ):
        self.classifer = classifer
        self.object_detector = object_detector
        self.locations = locations
        self.processed_images = processed_images
        self.file_types = file_types
        self.found_files = []
    
    def get_image_files(self, base_dir, file_types=None):
        if not file_types:
            file_types = self.file_types

        for root, _, files in os.walk(base_dir, topdown = False):
            for name in files:
                fullpath = os.path.join(root, name)
                if os.path.splitext(fullpath)[-1].upper() in file_types:
                    self.found_files.append(fullpath)
        return self.found_files

    def set_directory(self, directory):
        self.get_image_files(directory)

    def get_total_files(self):
        return len(self.found_files)

    def dummy_callback(self, image_file, state):
        print(image_file, state)

    def stop(self):
        self.processed_images.stop()

    def scan(self, reprocess=False, find_hdr=True, processed_file_callback=None):
        self.processed_images.start()
        if not processed_file_callback:
            processed_file_callback = self.dummy_callback

        with ThreadPoolExecutor(max_workers=32) as executor:
            _ = [
                executor.submit(
                    self.process_single_image_thread,
                    image_file=image_file, 
                    reprocess=reprocess, 
                    find_hdr=find_hdr, 
                    processed_file_callback=processed_file_callback
                )
                for image_file in self.found_files
            ]

            # I need to check for bad results in all of these:
            #wait(threads, return_when=ALL_COMPLETED)
        processed_file_callback('All', 'done')
        self.processed_images.stop()

    def process_single_image_thread(self, image_file, reprocess, find_hdr, processed_file_callback):
        processed_file_callback(image_file, 'start')

        if find_hdr:
            hdr_checker = HDRFinder(self.processed_images)

        if self.processed_images.check_if_processed(image_file) and not reprocess:
            processed_file_callback(image_file, 'already_processed')
            return

        metadata = self.process_image(image_file)

        self.processed_images.add(metadata)
        if find_hdr:
            hdr_checker.check(metadata)

        self.processed_images.commit()
        processed_file_callback(image_file, 'end')

    def process_image(self, filename, classify=True, detect_objects=True, get_location=True):
        image = Image(filename)    
        detected_objects = self.object_detector.detect(image) if self.object_detector and detect_objects else None
        image_classification = self.classifer.classify_image(image) if self.classifer and classify else None
        location = self.locations.get_location_at_timestamp(image.get_photo_date()) if self.locations and get_location else None

        p = ProcessedImage(
            filename=filename,
            classification=image_classification,
            detected_objects=detected_objects,
            location=location,
            date_taken=image.get_photo_date(),
            exif_data = image.get_json_safe_exif(),
            bracket_shot_count = image.bracket_shot_count,
            bracket_mode=image.bracket_mode,
            bracket_exposure_value=image.bracket_exposure_value,
            thumbnail=image.get_thumbnail().decode('utf-8')
        )

        return p

class MultiDirectoryWorker(DirectoryWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_directory(self, directories):
        if type(directories) == list:
            for directory in directories:
                self.found_files = self.found_files + self.get_image_files(directory)
        else:
            super().set_directory(directories)
