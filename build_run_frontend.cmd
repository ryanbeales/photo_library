docker build --pull --rm -f "Dockerfile_Frontend" -t photofrontend:latest "."
docker run -it --rm -p 3000:3000 photofrontend:latest
docker container prune -f
docker images prune
