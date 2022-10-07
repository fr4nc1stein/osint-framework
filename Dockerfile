FROM python:3.8-slim-buster

LABEL maintainer = "laet4x"
LABEL website="laet4x.com"
LABEL desc="Docker for OSIF"

WORKDIR /osif

RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install git build-essential -y
RUN apt-get install libmagic1 -y

COPY requirements.txt requirements.txt
COPY .env .env
RUN pip3 install -r requirements.txt
RUN pip3 install --user --upgrade git+https://github.com/twintproject/twint.git@origin/master#egg=twint

COPY . .

CMD [ "python3", "-B" , "main.py"]