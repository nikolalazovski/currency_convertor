# Currency Exchange Rate Service

This project is implemntation of a currency converter service.

## Local dev service

To run local service for development purposes, execute the following script after you clone the repository.

```bash
$ python3 -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt
(env) $ export FLASK_APP=kiwi_currency
(env) $ export FLASK_ENV=development
(env) $ flask init-db-random
(env) $ flask run
```

Keep in mind that this will populate the default sqlite database with random exchange rates.
If you want to connect to a different database system, please define the DATABASE_URL env variable.
