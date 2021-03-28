import os
from datetime import datetime

import pytest

from currency_convertor import cache, create_app, db, init_db
from currency_convertor.currency.models import ConversionRate
from currency_convertor.tinycache import TinyCache

with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "PERIODIC_TASK_PERIOD": 240,
        }
    )

    # create the database and load test data
    with app.app_context():
        init_db(real_data=False)

        for sql_insert in _data_sql.split(";"):
            db.session.execute(sql_insert)
            db.session.commit()

        # update the records as been created in this moment
        db.session.query(ConversionRate).filter().update({"created": datetime.utcnow()})
        db.session.commit()

        cache.invalidate_all()

    yield app


@pytest.fixture
def appwsgi():
    """Create and configure a new app instance for each test."""
    from currency_convertor.wsgi import app as wsgiapp

    # create the app with common test config
    wsgiapp = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    # create the database and load test data
    with wsgiapp.app_context():
        init_db(real_data=False)

        for sql_insert in _data_sql.split(";"):
            db.session.execute(sql_insert)
            db.session.commit()

        cache.invalidate_all()

    yield wsgiapp


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
