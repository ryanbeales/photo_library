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


class Worker(object):
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
        self.image_files = self.get_image_files(directory)

    def get_total_files(self):
        return len(self.image_files)

    def dummy_callback(self, image_file, state):
        print(image_file, state)

    def get_add_queue_depth(self):
        return self.processed_images.get_add_queue_depth()
    def get_hdr_queue_depth(self):
        return self.processed_images.get_add_queue_depth()


    def scan(self, reprocess=False, find_hdr=True, processed_file_callback=None):
        if not processed_file_callback:
            processed_file_callback = self.dummy_callback

        with ThreadPoolExecutor(max_workers=32) as executor:
            _ = [
                executor.submit(
                    self.process_single_photo,
                    image_file=image_file, 
                    reprocess=reprocess, 
                    find_hdr=find_hdr, 
                    processed_file_callback=processed_file_callback
                )
                for image_file in self.image_files
            ]

            # I don't think I need this...
            #wait(threads, return_when=ALL_COMPLETED)
        processed_file_callback('All', 'done')

    def process_single_photo(self, image_file, reprocess, find_hdr, processed_file_callback):
        processed_file_callback(image_file, 'start')

        worker = MetadataWorker(self.locations, self.classifer, self.object_detector)
        if find_hdr:
            hdr_checker = HDRFinder(self.processed_images)

        if self.processed_images.check_if_processed(image_file) and not reprocess:
            processed_file_callback(image_file, 'already_processed')
            return

        metadata = worker.process_image(image_file)

        self.processed_images.add(metadata)
        if find_hdr:
            hdr_checker.check(metadata)

        self.processed_images.commit()
        processed_file_callback(image_file, 'end')


class MetadataWorker(object):
    def __init__(self, locations_source, classifier, object_detector):
        self.locations = locations_source
        self.classifier = classifier
        self.object_detector = object_detector

    def process_image(self, filename, classify=True, detect_objects=True, get_location=True):
        image = Image(filename)    
        detected_objects = self.object_detector.detect(image) if self.object_detector and detect_objects else None
        image_classification = self.classifier.classify_image(image) if self.classifier and classify else None
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