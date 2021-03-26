# Currency Exchange Rate Service

This project is implemntation of a currency converter service.

## Running the dev API REST service locally

To run service locally for development purposes (without the other services), do the following in the folder where you have cloned this repository:

```bash
$ python3 -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt
(env) $ export FLASK_APP=kiwi_currency
(env) $ export FLASK_ENV=development
(env) $ flask init-db-dev
(env) $ flask run
```

Keep in mind that this will leave the default sqlite database with no exchange rates.
If you want to connect to a different database system, please define the `DATABASE_URL` env variable.

For example, if you have a postgres database, then the `DATABASE_URL` should be defined as:

```bash
DATABASE_URL=postgresql://[DB_USER]:[DB_PASS]@[DB_HOST]:[DB_PORT]/[DB_NAME]
```

## Running full solution

Before you run the entire solution via docker-compose, please create an `.env` file containing the following variables:

```bash
FLASK_APP=kiwi_currency
# production - the REST API will run through gunicorn wsgi
# development - the app will run with 'flask run'
FLASK_ENV=< production | development >
# Either file can be used, one is used for dev and the other is production optimized
DOCKER_FILE=< kiwi_currency/Dockerfile | kiwi_currency/Dockerfile.prod >

# Database credentials & variables
DATABASE=postgres
DATABASE_URL=postgresql://[DB_USER]:[DB_PASS]@[DB_HOST]:[DB_PORT]/[DB_NAME]
POSTGRES_USER=[DB_USER]
POSTGRES_PASSWORD=[DB_PASS]
POSTGRES_DB=[DB_NAME]
SQL_HOST=db
SQL_PORT=[DB_PORT]


# Template for the Currency Service API
CURRENCY_API_URL_TEMPLATE=https://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}
# The ID you got from the API service explained before
CURRENCY_API_ID=[The ID you got from the API service explained before]
# this is the time period for the periodic task executed by celery worker
PERIODIC_TASK_PERIOD=240

RABBITMQ_DEFAULT_USER=[RABBITMQ_USER]
RABBITMQ_DEFAULT_PASS=[RABBITMQ_PASS]
CELERY_BROKER_URL=amqp://[RABBITMQ_USER]:[RABBITMQ_PASS]@broker-rabbitmq//

```
