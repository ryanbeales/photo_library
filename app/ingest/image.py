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

    def load_file(self, filename):
        self.load_exif()

        logger.debug(f'Getting date taken for {filename}')
        try:
            self.date_taken = datetime.strptime(self.get_exif()['EXIF:DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
        except:
            logger.warning(f'unable to get date from exif data in {filename}, using file date')
            self.date_taken = datetime.fromtimestamp(os.stat(filename).st_ctime)

        self.extension = os.path.splitext(filename)[-1].upper()
        if self.extension in ['.JPG', '.JPEG']:
            self.load_jpeg_file(filename)
        elif self.extension in ['.CR2', '.CR3']:
            self.load_raw_file(filename)
        else:
            logger.debug(f"don't know how to open {filename}")
            raise Exception(f"I don't know how to open {self.extension}, sorry.")


    def load_jpeg_file(self, filename):
        logger.debug(f'Opening jpeg file with PIL {filename}')
        self.filetype = 'JPEG'
        self.img = PIL_Image.open(filename)
        
    def load_raw_file(self, filename):
        # Load image data in as a PIL object
        self.filetype = 'RAW'
        with rawpy.imread(filename) as raw:
            logger.debug(f'opening raw file: {filename}')
            self.img = PIL_Image.open(BytesIO(raw.extract_thumb().data))

    def load_exif(self):
        with ExifTool() as e:
            logger.debug(f'sending {self.filename} to exiftool')
            try:
                self.exif_data = e.get_metadata(self.filename)
                logger.debug(f'successfully loaded exif on {self.filename}')
            except:
                logger.error(f'error loading exif on {self.filename}')


    def get_exif(self):
        return self.exif_data
    
    def get_json_safe_exif(self):
        logger.debug(f'Generating json safe exif for {self.filename}')
        results = {k: str(v) for k,v in self.get_exif().items() }
        logger.debug(f'Finished generating json safe exif for {self.filename}')
        return results

    def get_photo_date(self):
        return self.date_taken

    def crop(self, region):
        return self.img.crop(region)

    def resize(self, size):
        return self.img.resize(size)
    
    def get_image_object(self):
        return self.img
    
    def get_thumbnail(self, long_edge_size=512):
        logger.debug(f'generating thumbnail for {self.filename}')
        self.img.thumbnail((long_edge_size,long_edge_size))
        buffered = BytesIO()
        self.img.save(buffered, format="JPEG")
        result = base64.b64encode(buffered.getvalue()).decode('utf-8')
        logger.debug(f'generated thumbnail for {self.filename}')
        return result

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
