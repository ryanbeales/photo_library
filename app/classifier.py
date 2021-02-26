import numpy as np
import tensorflow as tf # TF2
import psutil

class Classifier(object):
    def __init__(self, model_path, labels_file):
        self.interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=psutil.cpu_count())
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.floating_model = self.input_details[0]['dtype'] == np.float32

        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

        self.input_mean = 127.5
        self.input_std = 127.5

        with open(labels_file, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]

    def get_image_file(self, img):
       return img.resize((self.width, self.height))
    
    def classify_image(self, imgfile):
        img = self.get_image_file(imgfile)
        return self.classify(img)
    
    def classify_image_region(self, img, region):
        im_width, im_height = img.size
        ymin, xmin, ymax, xmax = tuple(region)
        img_region = img.crop((xmin * im_width, ymin * im_height, xmax * im_width, ymax * im_height)).resize((self.width, self.height))
        return self.classify(img_region)

    def classify(self, img):
        input_data = np.expand_dims(img, axis=0)

        if self.floating_model:
            input_data = (np.float32(input_data) - self.input_mean) / self.input_std

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

        self.interpreter.invoke()

        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        results = np.squeeze(output_data)

        top_k = results.argsort()[-5:][::-1]

        returned_results = {self.labels[i]:results[i] for i in top_k}
        # for i in top_k:
        #     if self.floating_model:
        #         print('{:08.6f}: {}'.format(float(results[i]), self.labels[i]))
        #     else:
        #         print('{:08.6f}: {}'.format(float(results[i] / 255.0), self.labels[i]))

        # print('time: {:.3f}ms'.format((stop_time - start_time) * 1000))
        return returned_results