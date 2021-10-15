# Description
This is a work in progress. There's lots of scary python in here and it's a giant monorepo of ideas. There is a plan however.
It's a spare time project however it's taking a lot of time so it's not finished yet.

# What is it?
This is a set of apps that will:
- Ingest new photo metadata from a NAS (put there by https://github.com/ryanbeales/sd_card_copier)
- Match up GPS locations by time from exported Google Location histories (or other sources, such at GPX files)
- A static html map generator of photo locations using Python + Folium
- Object Detection / Classification via Tensorflow of those images
- HDR detection and processing (eg: Look for three files in sequence, with -1,0,+1 exposure compensations)
- Photo metadata/thumbnail server written in Python + Flask + GraphQL
- React front end to query and view the server.

# Future Plans
- Progress down this path?
- Use alternate workflows for ingestion/processing like Airflow?
- Switch to K8s

# Classification notes
Using multiple of the the hosted models here:
https://www.tensorflow.org/lite/guide/hosted_models

Run it accross photos:
```
docker container prune
docker volume rm crobnas
docker volume create crobnas -d local -o type=nfs -o device=:/stash -o o=addr=crobnas.local,rw
docker run -it -v crobnas:/work/stash photoclassifier:latest
```