Using multiple of the the hosted models here:
https://www.tensorflow.org/lite/guide/hosted_models

Classify each image

Using tensorflow/tensorflow docker container which runs on CPU, load the above model, and run against a test image.


Run it accross photos:
```
docker container prune
docker volume rm crobnas
docker volume create crobnas -d local -o type=nfs -o device=:/stash -o o=addr=crobnas.local,rw
docker run -it -v crobnas:/work/stash photoclassifier:latest
```

Nasnet isn't finding humans...

Maybe cut of things that aren't 90% sure?

Current flow is: