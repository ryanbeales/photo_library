# Image signatures:
#   Once you have a fingerprint, use https://en.wikipedia.org/wiki/Earth_mover%27s_distance to calculate similarity
# Test if similar image:
#   Greyscale, blur, scale to 16x16 for a 256bit fingerprint, xor values and compare left over values for a guess at similar images
# Test if part of a panorama:
#   Grayscale it, blur it, scale it down to 16x16 and you get a 256bit signature
#   Save the image in 16x16 columns of data, then you can compare columns for potential matches with a column from another image
#   The more columns that match, the higher chance they are part of a panorama.
#   Also - if the filesnames/dates are very close to each other then higher chance they are part of a panorama set
# Test if part of HDR set:
#   Same greyscale, blur, scale down to 16x16 and 256bit signature
#   However, normalize to 50% grey - then you can compare images of different luminence/brightness
#
# With that info we can fire off hugin or something to autoprocess photos into tiffs, then bring in to photoshop/lightroom for 
# further processing

from PIL import Image as PIL_Image
from PIL import ExifTags
import tensorflow as tf # TF2
from datetime import datetime
import rawpy
import os
from io import BytesIO
import base64

class Image(object):
    def __init__(self, filename):
        self.filename = filename
        self.location = None
        self.date_taken = None
        self.load_file(filename)

    def load_file(self, filename):
        self.extension = os.path.splitext(filename)[-1].upper()
        if self.extension in ['.JPG', '.JPEG']:
            self.load_jpeg_file(filename)
        elif self.extension in ['.CR2', '.CR3']:
            self.load_raw_file(filename)
        else:
            raise Exception(f"I don't know how to open {self.extension}, sorry.")

    def load_jpeg_file(self, filename):
        self.img = PIL_Image.open(filename)
        self.make_exif(self.img.getexif())
        self.date_taken = datetime.strptime(self.get_exif()['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')

    def load_raw_file(self, filename):
        # Load image data in as a PIL object
        with rawpy.imread(filename) as raw:
            #rgb = raw.postprocess()
            # Thumbnail is 300x300 so ok for classification
            thumbnail = PIL_Image.open(BytesIO(raw.extract_thumb().data))
        self.img = thumbnail
        self.make_exif(self.img.getexif())

        # Save the date taken for later use
        self.date_taken = datetime.strptime(self.get_exif()['DateTime'], '%Y:%m:%d %H:%M:%S')

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
        thumb = self.img.resize((32,32))
        buffered = BytesIO()
        thumb.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue())