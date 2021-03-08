import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import tensorflow_hub as hub
import numpy as np

import logging
logger = logging.getLogger(__name__)


class ObjectDetector:
    # https://github.com/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
    def __init__(self, model):
        module_handle = model
        self.detector = hub.load(module_handle).signatures['default']
        self.input_mean = 127.5
        self.input_std = 127.5

    def detect(self, img, confidence_cutoff=0.2):
        input_data = np.expand_dims(img.get_image_object(), axis=0)
        input_data = (np.float32(input_data) - self.input_mean) / self.input_std
        input_data = tf.convert_to_tensor(input_data, dtype=tf.float32)

        result = self.detector(input_data)
        result = {key:value.numpy() for key,value in result.items()}

        # Get detected objects where it's higher than confidence_cutoff
        r = { 
            result['detection_class_entities'][i].decode('utf-8'): int(result['detection_scores'][i]*100) 
            for i in range(len(result['detection_scores'])) 
            if result['detection_scores'][i] >= confidence_cutoff
        }
        return r
