docker context use crobbox
docker build --pull --rm -f "Dockerfile" -t photoclassifier:latest "."
docker run -it -v crobnas:/work/stash --env PHOTO_REPROCESS=x photoclassifier:latest
docker container prune -f
docker images prune
