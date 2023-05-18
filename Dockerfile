FROM python:3.10

RUN printf "\n####\nStart: $(date)\n####\n"

RUN useradd -ms /bin/bash scraper
WORKDIR /home/scraper

RUN apt update
RUN apt install gcc python3-pip python3 python3-setuptools -y

COPY requirements.txt ./

RUN python3 -m pip install --upgrade setuptools pip --no-warn-script-location --no-input
RUN python3 -m pip install -r requirements.txt --no-warn-script-location --no-input

COPY .env ./
COPY setup.py ./

RUN python3 setup.py

RUN python3 -m playwright install-deps
USER scraper 

RUN python3 -m playwright install
RUN python3 -m coreferee install en

COPY ./API/ ./API/
COPY ./Core/ ./Core/
COPY ./EndScripts/ ./EndScripts/
COPY ./Extensions/ ./Extensions/
COPY ./External/ ./External/
COPY ./Plugins/ ./Plugins/
COPY ./Settings/ ./Settings/
COPY ./Tests/ ./Tests/
COPY ./Utils/ ./Utils/
COPY ./gui.py ./
COPY ./decompile.sh ./
COPY ./compile.py ./

USER root
RUN chown -R scraper ./
USER scraper

RUN export PATH=$PATH:/home/scraper/.local/bin

RUN export $(cat .env | grep "^[^#]" | xargs)

RUN ./decompile.sh
#RUN python3 compile.py

ENTRYPOINT ["python", "gui.py"]