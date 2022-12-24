FROM mcr.microsoft.com/playwright/python:v1.28.0-focal

RUN useradd -ms /bin/bash scraper
WORKDIR /home/scraper

RUN apt update
RUN apt install gcc python3-pip python3 python3-setuptools -y

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
COPY ./decompile.sh ./
COPY ./compile.py ./
COPY .env ./
COPY requirements.txt ./
COPY setup.py ./

RUN chown -R scraper ./API/
RUN chown -R scraper ./Core/
RUN chown -R scraper ./EndScripts/
RUN chown -R scraper ./Extensions/
RUN chown -R scraper ./External/
RUN chown -R scraper ./Plugins/
RUN chown -R scraper ./Settings/
RUN chown -R scraper ./Tests/
RUN chown -R scraper ./Utils/
RUN chown scraper ./cli.py
RUN chown scraper ./decompile.sh
RUN chown scraper ./compile.py
RUN chown scraper .env 
RUN chown scraper requirements.txt
RUN chown scraper setup.py

USER scraper

RUN export PATH=$PATH:/home/scraper/.local/bin

RUN export $(cat .env | grep "^[^#]" | xargs)

RUN python3 -m pip install -r requirements.txt --no-warn-script-location

RUN python3 setup.py

RUN python3 -m playwright install

#RUN ./decompile.sh
#RUN python3 compile.py

ENTRYPOINT ["python", "cli.py"]