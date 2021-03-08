docker build --pull --rm -f "Dockerfile_Ingest" -t photoingest:latest "."
docker run -it -v crobnas:/work/stash --env PHOTO_REPROCESS=x photoingest:latest
docker container prune -f
docker images prune
