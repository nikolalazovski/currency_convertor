# pull official base image
FROM python:3.8.1-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# upgrade pip
RUN pip install --upgrade pip

# copy the distribution
COPY dist/kiwi_currency-1.0.6.dev0-py3-none-any.whl .
RUN pip install kiwi_currency-1.0.6.dev0-py3-none-any.whl
