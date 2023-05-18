#docker run -ti --rm --name scraper -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -d scraper
xhost +local:docker
docker-compose up
xhost -local:docker
