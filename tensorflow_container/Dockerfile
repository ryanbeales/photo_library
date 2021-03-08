FROM tensorflow/tensorflow

RUN mkdir /work

RUN apt install -y wget vim

RUN mkdir /work/nasnet/
WORKDIR /work/nasnet/
RUN wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/model_zoo/upload_20180427/nasnet_large_2018_04_27.tgz
RUN tar xvzf nasnet_large_2018_04_27.tgz
RUN rm nasnet_large_2018_04_27.tgz

RUN mkdir /work/object_detector/
WORKDIR /work/object_detector
RUN wget https://storage.googleapis.com/tfhub-modules/google/faster_rcnn/openimages_v4/inception_resnet_v2/1.tar.gz
RUN tar xvzf 1.tar.gz
RUN rm 1.tar.gz

RUN pip install pillow psutil tensorflow_hub geopy rawpy folium scipy pyexiftool progress dataclasses
RUN apt install -y exiftool

COPY app /work/app

WORKDIR /work/app
ENTRYPOINT [ "python", "/work/app/app.py" ]
