# Currency Exchange Rate Service

This project is an implemntation of a currency converter service.

## REST API Definitions

There are two REST endpoints that the service exposes:

```http
GET /
```

This endpoint will return a list the currencies supported by the service.

```javascript
{
  "data" : list
}
```

The second endpoint is the endpoint to perform conversion from one currency rate to another.

```http
GET,POST /convert/<string:from_currency>/<string:to_currency>/<amount>
```

The response of this endpoint:


| Parameter | Type | Description |
| :--- | :--- | :--- |
| `from_currency` | `string` | **Required**. The origin currency |
| `to_currency` | `string` | **Required**. The target currency |
| `amount` | `float` | **Required**. The original amount that was sent by the client |
| `converted` | `float` | **Required**. The amount converted in the target currency |

## Possible architectures

There are two architectures considered:

- First solution
    * Flask for the REST API service + SQLAlchemy ORM for database access
    * Gunicorn WSGI server
    * Celery worker for periodic task for fetching the exchange rates + RabittMQ as a broker
    * Postgres database to store the current and historical exchange rates
    * Prometheus as a monitoring database
    * Grafana as a monitoring dashboard service using the Prometheus as a data source

- Second solution based in AWS (TO BE DONE!)
    * API Gateway for REST API
    * Lambda functions as hooks for the API
    * Dynamo DB to store the exchange rates (DAX can be used as well to cache some of the queries)
    * AWS EventBridge + Lambda to run the periodic task for fetching the exchange rates from external service

## Running the dev API REST service locally

To run service locally (not necessarily with other services), do the following in the folder where you have cloned this repository (Note: You can populate your database with real exchange currencies if you perdorm the first step of the section [Running full solution with docker compose](##running-full-solution-with-docker-compose) and export the env variables `CURRENCY_API_URL_TEMPLATE` and `CURRENCY_API_ID`):

```bash
$ python3 -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements-dev.txt
(env) $ export FLASK_APP=kiwi_currency
(env) $ export FLASK_ENV=development
(env) $ flask init-db
(env) $ flask run
```

Keep in mind that this will leave the default `sqlite` database with no exchange rates records.
If you want to connect to a different database system, please define the `DATABASE_URL` env variable.

For example, if you have a postgres database, then the `DATABASE_URL` should be defined as:

```bash
DATABASE_URL=postgresql://[DB_USER]:[DB_PASS]@[DB_HOST]:[DB_PORT]/[DB_NAME]
```

## Running full solution with docker compose

First, you have to get an API ID from the service providing the exchange rates. Please visit [currencyconverterapi](https://free.currencyconverterapi.com/) in order to get your API ID.


Second, before you run the entire solution via docker-compose, please create an `.env` file in the root folder containing the following variables:

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


# Template for the Currency Service API. Do not change this variable!
CURRENCY_API_URL_TEMPLATE=https://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}
# The ID you got from the API service explained before
CURRENCY_API_ID=[The ID you got from the API service explained before]
# this is the time period(in seconds) for the periodic task executed by celery worker
PERIODIC_TASK_PERIOD=240

# RabbitMQ credentials & URL
RABBITMQ_DEFAULT_USER=[RABBITMQ_USER]
RABBITMQ_DEFAULT_PASS=[RABBITMQ_PASS]
CELERY_BROKER_URL=amqp://[RABBITMQ_USER]:[RABBITMQ_PASS]@broker-rabbitmq//

```

To run the entire solution, run:

```bash
docker-compose up -d --build
```

You can access the REST API service through [http://localhost:5000](http://localhost:5000), and the Grafana monitoring instance through [http://localhost:3000](http://localhost:3000).


To get all the containers stopped, run:

```bash
docker-compose down -v
```
