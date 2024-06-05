FROM python:3.10

WORKDIR /code/

COPY . /code/

RUN pip install -r requirements.txt