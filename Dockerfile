FROM mcr.microsoft.com/playwright/python:v1.28.0-focal

RUN useradd -ms /bin/bash scraper
USER scraper

WORKDIR /home/scraper
RUN export PATH=$PATH:/home/scraper/.local/bin

COPY .env ./
RUN export $(cat .env | grep "^[^#]" | xargs)

COPY requirements.txt ./
RUN python3 -m pip install -r requirements.txt --no-warn-script-location

COPY setup.py ./
RUN python3 setup.py

RUN python3 -m playwright install

COPY ./API/ ./API/
COPY ./Core/ ./Core/
COPY ./EndScripts/ ./EndScripts/
COPY ./Extensions/ ./Extensions/
COPY ./External/ ./External/
COPY ./Plugins/ ./Plugins/
COPY ./Settings/ ./Settings/
COPY ./Tests/ ./Tests/
COPY ./Utils/ ./Utils/
COPY ./cli.py ./

#COPY ./compile.py ./
#RUN python3 compile.py

ENTRYPOINT ["python", "cli.py"]