import numpy as np
import tensorflow as tf # TF2
import tensorflow_hub as hub
from tensorflow.keras.applications.xception import decode_predictions
import psutil


class Xception:
    def __init__(self):
        self.model=tf.keras.applications.xception.Xception(weights='imagenet',include_top=True)
    
    def classify(self, imagefile):
        img=tf.keras.preprocessing.image.load_img(imagefile,target_size=(299,299))
        img=tf.keras.preprocessing.image.img_to_array(img)

        img=tf.keras.applications.xception.preprocess_input(img)
        predictions=self.model.predict(np.array([img]))
        return decode_predictions(predictions,top=5)