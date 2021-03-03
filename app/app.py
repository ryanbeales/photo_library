# Example https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py

import os
import requests
import json
import time
from datetime import timedelta
import psutil
from glob import glob
import json

from pprint import pprint

from image import Image
from classifier import Classifier
from objectdetector import ObjectDetector
from locations import Locations
from hdr_finder import HDRFinder
from map_maker import MapMaker
from processed_images import ProcessedImages


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
                'bracket_shot_count': image.bracket_shot_count,
                'bracket_mode': image.bracket_mode,
                'bracket_exposure_value': image.bracket_exposure_value,
                'thumbnail': image.get_thumbnail().decode('utf-8')
        }


def get_image_files(base_dir, file_types=['.CR2', '.CR3', '.JPG']):
    found_files = []
    for root, dirs, files in os.walk(base_dir, topdown = False):
       for name in files:
          fullpath = os.path.join(root, name)
          if os.path.splitext(fullpath)[-1].upper() in file_types:
              found_files.append(fullpath)
    return found_files


if __name__ == '__main__':
    classify=False
    reprocess=False

    print('loading location data')
    locations = Locations(history_file=r'/work/stash/Backup/Google Location History/Location History.json')


    if classify:
        print('loading nasnet')
        nasnet = Classifier('/work/nasnet/nasnet_large.tflite', '/work/nasnet/labels.txt')

        print('loading object_detector')
        object_detector = ObjectDetector('/work/object_detector')
    else:
        nasnet = None
        object_detector = None

    image_files = get_image_files(r'/work/stash/Photos/Canon EOS M5/2018')

    worker = MetadataWorker(locations, nasnet, object_detector)

    processed_images = ProcessedImages('/work/stash/src/classification_output/image_metadata.json')

    hdr_checker = HDRFinder(processed_images)

    count=0
    average_image_time = 1
    for image_file in image_files:
        start_time = time.time()

        if processed_images.retrieve(image_file) and not reprocess:
            print(f"Already processed {image_file}, skipping")
            continue

        metadata = worker.process_image(image_file, classify=classify, detect_objects=classify)

        processed_images.add(metadata)
        hdr_checker.check(metadata)


        end_time = time.time()
        print(f"finished processing {image_file}")
        print("Time on image: ", end_time-start_time)

        images_left = len(image_files) - count
        average_image_time = (average_image_time + (end_time - start_time)) / 2
        count = count + 1
        time_left = timedelta(seconds=average_image_time * images_left)
        print(f"Approximately {time_left} left")
    
    processed_images.save()

    print('Generating map')
    m = MapMaker(processed_images)
    m.make_map('/work/stash/src/classification_output/image_map.html')
    print('Done!')