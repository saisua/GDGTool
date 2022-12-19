FROM mcr.microsoft.com/playwright/python:v1.28.0-focal

RUN useradd -ms /bin/bash scraper
USER scraper

WORKDIR /home/scraper
RUN export PATH=$PATH:/home/scraper/.local/bin

COPY . .

RUN export $(cat .env | grep "^[^#]" | xargs)

RUN python3 -m pip install -r requirements.txt --no-warn-script-location
RUN python3 setup.py
RUN python3 -m playwright install
#RUN python3 compile.py

CMD ["python3", "cli.py"]