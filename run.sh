#docker run -ti --rm --name scraper -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -d scraper
echo "This will NOT build the docker"
xhost +local:docker
docker-compose up -d && \
docker exec -it scraper python3 /home/scraper/gui.py $@
xhost -local:docker
