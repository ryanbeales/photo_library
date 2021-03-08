# Test if similar image:
#   Greyscale, blur, scale to 128x128, get the histogram (we could just use the full histogram here?)
#   Very low wasserstein_distance (<2? for 128x128 image) means it's probably almost the same image of the same thing.
#
# Test if part of a panorama:
#   Grayscale it, blur it, scale it down to 16x16 and you get a 256bit signature
#   Save the image in 16x16 columns of data, then you can compare columns for potential matches with a column from another image
#   The more columns that match, the higher chance they are part of a panorama.
#   Also - if the filesnames/dates are very close to each other then higher chance they are part of a panorama set


# With that info we can fire off hugin or something to autoprocess photos into tiffs, then bring in to photoshop/lightroom for 
# further processing

from PIL import Image as PIL_Image
from PIL import ExifTags
from PIL import ImageOps as PIL_ImageOps
from PIL import ImageFilter as PIL_ImageFilter

import numpy as np

from datetime import datetime, timedelta

import rawpy

import os
from io import BytesIO
import base64

import scipy.stats as stats

from exiftool import ExifTool

import logging
logger = logging.getLogger(__name__)


class Image(object):
    def __init__(self, filename):
        self.filename = filename
        self.location = None
        self.date_taken = None
        self.load_file(filename)
        self.bracket_mode = 0
        self.bracket_shot_count = 1
        self.bracket_exposure_value = 0

    def load_file(self, filename):
        logger.debug(f'loading {filename}')
        self.extension = os.path.splitext(filename)[-1].upper()
        if self.extension in ['.JPG', '.JPEG']:
            self.load_jpeg_file(filename)
        elif self.extension in ['.CR2', '.CR3']:
            self.load_raw_file(filename)
        else:
            logger.debug(f"don't know how to open {filename}")
            raise Exception(f"I don't know how to open {self.extension}, sorry.")

    def load_jpeg_file(self, filename):
        self.img = PIL_Image.open(filename)
        self.make_exif(self.img.getexif())
        self.date_taken = datetime.strptime(self.get_exif()['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
        logger.debug(f'opened jpeg {filename} which was taken at {self.date_taken}')

    def load_raw_file(self, filename):
        # Load image data in as a PIL object
        with rawpy.imread(filename) as raw:
            logger.debug(f'opening raw file: {filename}')
            self.img = PIL_Image.open(BytesIO(raw.extract_thumb().data))
        with ExifTool() as e:
            logger.debug(f'sending {filename} to exiftool')
            self.exif_data = e.get_metadata(filename)[0]


        try:
            self.date_taken = datetime.strptime(self.get_exif()['EXIF:DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
        except:
            logger.warning(f'unable to get date from exif data in {filename}, using file date')
            self.date_taken = datetime.fromtimestamp(os.stat(filename).st_ctime)
            
        self.bracket_exposure_value = self.get_exif()['MakerNotes:BracketValue']
        self.bracket_mode = self.get_exif()['MakerNotes:BracketMode']
        if 'MakerNotes:AEBShotCount' in self.get_exif():
            self.bracket_shot_count = self.get_exif()['MakerNotes:AEBShotCount']
        else:
            self.bracket_shot_count = 3
        logger.debug(f'AEB data on {filename}: {self.bracket_mode}, {self.bracket_exposure_value}, {self.bracket_shot_count}')
        
    def get_exif(self):
        return self.exif_data
    
    def get_json_safe_exif(self):
        return {k: str(v) for k,v in self.get_exif().items() }
    
    def make_exif(self, e):
        self.exif_data = {
            ExifTags.TAGS[k]: v
            for k, v in e.items()
            if k in ExifTags.TAGS
        }

    def get_photo_date(self):
        return self.date_taken

    def crop(self, region):
        return self.img.crop(region)

    def resize(self, size):
        return self.img.resize(size)
    
    def get_image_object(self):
        return self.img
    
    def get_thumbnail(self):
        logger.debug(f'generating thumbnail for {self.filename}')
        thumb = self.img.resize((64,64))
        buffered = BytesIO()
        thumb.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue())

    def get_fingerprint(self):
        logger.debug(f'generating fingerprint for {self.filename}')
        # Blur, resize, greyscale, autocontrast
        blurred = self.img.filter(PIL_ImageFilter.GaussianBlur(radius=3))
        greyscale = PIL_ImageOps.grayscale(blurred)
        autocontrast = PIL_ImageOps.autocontrast(greyscale, cutoff=5) # remove 5% from top and bottom of histogram
        return autocontrast.histogram()

    def compare(self, image2):
        logger.debug(f'comparing {self.filename} and {image2.filename}')
        return stats.wasserstein_distance(self.get_fingerprint(), image2.get_fingerprint())
