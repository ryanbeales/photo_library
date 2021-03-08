docker build --pull --rm -f "Dockerfile_Locations" -t photolocations:latest "."
docker run -it -v crobnas:/work/stash --env PHOTO_REPROCESS=x photolocations:latest
docker container prune -f
docker images prune
