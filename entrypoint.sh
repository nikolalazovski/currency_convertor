#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

flask init-db

if [ "$FLASK_ENV" = "production" ]
then
    gunicorn -w 4 -b 0.0.0.0:5000 kiwi_currency.wsgi:app
else
    flask run -h 0.0.0.0
fi
