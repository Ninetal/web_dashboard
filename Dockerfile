FROM python:3.10

RUN apt-get update && apt-get install build-essential libpq-dev -y
RUN pip install --upgrade pip setuptools

COPY . /opt/web_dashboard/
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR /opt/web_dashboard/


