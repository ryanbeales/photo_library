docker build --pull --rm -f "Dockerfile_Ingest" -t photoingest:latest "."
docker build --rm -f "Dockerfile_Mapmaker" -t photomapmaker:latest "."
docker run -it -v crobnas:/work/stash photomapmaker:latest
docker container prune -f
docker images prune
