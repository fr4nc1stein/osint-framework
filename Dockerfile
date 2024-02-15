FROM python:3.11.8-slim-bullseye

LABEL maintainer = "laet4x|cadeath"
LABEL website="laet4x.com"
LABEL desc="Docker for OSIF"

WORKDIR /osif

RUN apt-get update && \
    apt-get upgrade -yq
RUN apt-get -y install build-essential git \
        gcc mono-mcs libmagic1 && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt requirements.txt
COPY .env.example .env
RUN pip3 install -r requirements.txt
RUN pip3 install --user --upgrade git+https://github.com/twintproject/twint.git@origin/master#egg=twint

COPY . .

RUN chmod +x osif
CMD [ "./osif"]