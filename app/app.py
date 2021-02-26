# Example https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/examples/python/label_image.py


import os
import requests
import json
import time
import psutil
from glob import glob

from pprint import pprint


from image import Image
from classifier import Classifier
from objectdetector import ObjectDetector
from locations import Locations


# https://letmaik.github.io/rawpy/api/ for raw files.

# Something for maps? Searching based on class? area?

# TODO:
# - Image input class (subclasses for raw/jpg) so we're not just passing around file names and reopening
# - Processed image class, containing all the metadata and thumbnail. From that we can generate an output (json?) or a map?
# - Figure out how to do this over time, rerun with better classifications, better location data, etc.
# - Fix misclassification of rivers/waterfalls as Geysers.
# - Fix get confidence scores for each of the objects detected.
# - Fail gracefully if anything goes missing / is wrong (location data, unreadable files, etc)
# - Let tensorflow download models from hub? Maybe after we're confident it all works.
# - This https://stackoverflow.com/a/13517771 or https://en.wikipedia.org/wiki/Earth_mover%27s_distance to find similar images.
# - A way to query/display all this...
# - A better file globber to walk the photos directory and classify things
# Done:
# - Load image data from NAS - DONE
# - Load location data from NAS - DONE
# - Test speed on Fast puter: DONE
#   - laptop is 8 seconds per image (12 threads)
#   - desktop is about 4.5seconds per image (24 threads)




if __name__ == '__main__':
    print('loading location data')
    locations = Locations(history_file=r'/work/stash/Backup/Google Location History/Location History.json')

    # Load Models:
    print('loading nasnet')
    nasnet = Classifier('/work/nasnet/nasnet_large.tflite', '/work/nasnet/labels.txt')

    print('loading object_detector')
    object_detector = ObjectDetector('/work/object_detector')

    jpegs = glob('/work/stash/Photos/PiFrame/Photos/Amsterdam2019/*.jpg')
    for jpeg in jpegs:
        start_time = time.time()

        print('current file: ' + jpeg)
        image = Image(jpeg)

        detected_objects = object_detector.detect(image)
        image_classification = nasnet.classify_image(image)
        location = locations.get_location_at_timestamp(image.get_photo_date())

        print(f'Nasnet thinks the image is: {image_classification}')
        print(f"I think I can idenfiy these things: {set(detected_objects['detection_class_entities'])}")
        print(f'location data is : {location}')
        print(f'photo was taken at: {image.get_photo_date()}')

        end_time = time.time()
        print("Time on image: ", end_time-start_time)