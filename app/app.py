# Example https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py

import os
import requests
import json
import time
import psutil
from glob import glob
import json

from pprint import pprint

from image import Image
from classifier import Classifier
from objectdetector import ObjectDetector
from locations import Locations

class ProcessedImages(object):
    def __init__(self, saved_filename=None):
        self.saved_filename = saved_filename
        self.load()
        
    def load(self):
        if self.saved_filename:
            try:
                with open(self.saved_filename) as f:
                    self.images = json.load(f)
            except:
                self.images = {}

    def add(self, metadata):
        self.images[metadata['filename']] = metadata
    
    def retrieve(self, filename):
        if filename in self.images.keys():
            return self.images[filename]
        else:
            return None
    
    def save(self):
        with open(self.saved_filename, 'w') as f:
            f.write(json.dumps(self.images))


class MetadataWorker(object):
    def __init__(self, locations_source, classifier, object_detector):
        self.locations = locations_source
        self.classifier = classifier
        self.object_detector = object_detector

    def process_image(self, filename, classify=True, detect_objects=True, get_location=True):
        image = Image(image_file)    
        detected_objects = self.object_detector.detect(image) if detect_objects else None
        image_classification = self.classifier.classify_image(image) if classify else None
        location = locations.get_location_at_timestamp(image.get_photo_date()) if get_location else None

        return {
                'filename': filename, 
                'classification': image_classification, 
                'detected_objects': detected_objects, 
                'location': location, 
                'date_taken': str(image.get_photo_date()), 
                'exif_data': image.get_json_safe_exif(), 
                'thumbnail': image.get_thumbnail().decode('utf-8')
        }


if __name__ == '__main__':
    print('loading location data')
    locations = Locations(history_file=r'/work/stash/Backup/Google Location History/Location History.json')

    print('loading nasnet')
    nasnet = Classifier('/work/nasnet/nasnet_large.tflite', '/work/nasnet/labels.txt')

    print('loading object_detector')
    object_detector = ObjectDetector('/work/object_detector')

    image_files = glob(r'/work/stash/Photos/Canon EOS M6 II/2019/12/02/CR3/*.CR3')[:10] + glob(r'/work/stash/Photos/PiFrame/Photos/Amsterdam2019/*.jpg')[:10]

    worker = MetadataWorker(locations, nasnet, object_detector)

    processed_images = ProcessedImages('/work/stash/src/classification_output/image_metadata.json')
    reprocess = False

    for image_file in image_files:
        start_time = time.time()

        if processed_images.retrieve(image_file) and not reprocess:
            print(f"Already processed {image_file}, skipping")
            continue

        metadata = worker.process_image(image_file)

        end_time = time.time()
        print(f"finished processing {image_file}")
        pprint(metadata)
        processed_images.add(metadata)
        print("Time on image: ", end_time-start_time)
    
    processed_images.save()