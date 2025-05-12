FROM python:3.9.20

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements-dev.txt
