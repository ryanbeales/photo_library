docker build --pull --rm -f "Dockerfile_Ingest" -t photoingest:latest "."
docker run -it -v crobnas:/work/stash photoingest:latest
docker container prune -f
docker images prune
