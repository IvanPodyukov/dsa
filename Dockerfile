FROM python:3.10

RUN apt-get update && apt-get -y dist-upgrade
RUN apt install -y netcat-openbsd

WORKDIR /usr/src/studentProjects

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .

COPY . .

ENTRYPOINT ["/usr/src/studentProjects/entrypoint.sh"]