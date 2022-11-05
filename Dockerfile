FROM python:3.8-slim-buster

LABEL maintainer = "laet4x"
LABEL website="laet4x.com"
LABEL desc="Docker for OSIF"

WORKDIR /osif

RUN apt-get update && \
    apt-get -y install build-essential git \
        gcc mono-mcs libmagic1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY .env.example .env
RUN pip3 install -r requirements.txt
RUN pip3 install --user --upgrade git+https://github.com/twintproject/twint.git@origin/master#egg=twint

COPY . .

RUN chmod +x osif
# CMD [ "python3", "-B" , "main.py"]
CMD [ "./osif"]