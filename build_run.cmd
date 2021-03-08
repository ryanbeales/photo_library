docker context use default
docker build --pull --rm -f "Dockerfile_Ingest" -t photoclassifier:latest "."
docker run -it -v crobnas:/work/stash --env PHOTO_REPROCESS=x photoclassifier:latest
docker container prune -f
docker images prune
