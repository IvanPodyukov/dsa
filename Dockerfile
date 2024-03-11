FROM python:3.10

RUN apt-get update && apt-get -y dist-upgrade
RUN apt install -y netcat-openbsd
# set work directory
WORKDIR /usr/src/studentProjects
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .
# copy project
COPY . .

ENTRYPOINT ["/usr/src/studentProjects/entrypoint.sh"]