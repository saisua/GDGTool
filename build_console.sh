xhost +local:docker
docker-compose up --build -d && \
docker exec -it scraper /bin/bash
xhost -local:docker
docker stop scraper