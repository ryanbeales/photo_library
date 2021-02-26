import tensorflow_hub as hub

class ObjectDetector:
    # https://github.com/tensorflow/hub/blob/master/examples/colab/object_detection.ipynb
    def __init__(self, model):
        module_handle = model
        self.detector = hub.load(module_handle).signatures['default']

    def detect(self, img):
        result = self.detector(img.get_tensor_data())
        result = {key:value.numpy() for key,value in result.items()}
        return result
