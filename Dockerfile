FROM python:3.8-slim-buster

WORKDIR /osif

RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install build-essential -y
RUN apt-get install libmagic1 -y

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-B" , "main.py"]