xhost +local:docker
docker-compose up --build -d && \
docker exec -it scraper python3 /home/scraper/gui.py
xhost -local:docker
docker stop scraper