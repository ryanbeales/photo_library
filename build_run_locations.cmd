docker build --pull --rm -f "Dockerfile_Ingest" -t photoingest:latest "."
docker build --rm -f "Dockerfile_Locations" -t photolocations:latest "."
docker run -it -v crobnas:/work/stash photolocations:latest
docker container prune -f
docker images prune
