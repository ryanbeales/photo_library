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

class ImageMetadata(object):
    def __init__(self, filename, thumbnail, location, classification, detectedobjects):
        pass


class Image(object):
    def __init__(self, filename):
        self.filename = filename
        self.type = 'JPG' # or raw, or something
        self.location = None
        self.img = PIL_Image.open(filename)
        self.photo_date_tag = self.get_exif_tag_by_name('DateTimeOriginal')
        self.date_taken = None
            
    def get_exif(self):
        return self.img.getexif()

    def get_photo_date(self):
        if not self.date_taken:
            exif_data = self.img.getexif()
            self.date_taken = datetime.strptime(exif_data[self.photo_date_tag], '%Y:%m:%d %H:%M:%S')
        return self.date_taken

    def get_exif_tag_by_name(self, tagname):
        return list(ExifTags.TAGS.keys())[list(ExifTags.TAGS.values()).index(tagname)]

    def crop(self, region):
        return self.img.crop(region)

    def resize(self, size):
        return self.img.resize(size)

    def get_tensor_data(self):
        # We can probably do this better, without reopening.
        img = tf.io.read_file(self.filename)
        img = tf.image.decode_jpeg(img, channels=3)
        return tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]


    def get_metadata(self):
        return ImageMetadata(self.filename, None, self.location, None, None)
