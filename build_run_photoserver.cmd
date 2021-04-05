docker build --pull --rm -f "Dockerfile_Photoserver" -t photoserver:latest "."
docker run -it -v crobnas:/work/stash -p 5000:5000 photoserver:latest
docker container prune -f
docker images prune