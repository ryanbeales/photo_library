docker build --pull --rm -f "Dockerfile_Ingest" -t photoingest:latest "."
docker build --rm -f "Dockerfile_HDRFinder" -t photohdrfinder:latest "."
docker run -it -v crobnas:/work/stash photohdrfinder:latest
docker container prune -f
docker images prune