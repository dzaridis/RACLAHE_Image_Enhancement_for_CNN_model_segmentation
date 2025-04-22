FROM ubuntu:20.04

WORKDIR /dir

RUN mkdir /dir/input
RUN mkdir /dir/output
COPY . /dir


ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get install -y python3-pip
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt

ENTRYPOINT ["python3","/dir/__main__.py"]
