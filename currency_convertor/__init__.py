import os

import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy

from currency_convertor.tinycache import TinyCache
from prometheus_flask_exporter import PrometheusMetrics

__version__ = (1, 0, 7, "dev")

db = SQLAlchemy()
cache = TinyCache()
metrics = PrometheusMetrics.for_app_factory()


def get_env(key, default_value):
    return os.environ.get(key, default_value)


def create_app(test_config=None):
    """
    Factory method to create the Flask Kiwi Currency App.
    """

    # default configuration for the app
    default_config = {
        # can be used in case of sessions
        "SECRET_KEY": get_env("SECRET_KEY", "dev"),
        # database URI
        "SQLALCHEMY_DATABASE_URI": get_env("DATABASE_URL", None),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        # the template for the API currency exchange rates call
        "CURRENCY_APP_TEMPLATE": get_env("CURRENCY_API_URL_TEMPLATE", ""),
        # API ID given by the service
        "CURRENCY_API_ID": get_env("CURRENCY_API_ID", ""),
        # the period to refresh the currency exchange rates
        "PERIODIC_TASK_PERIOD": float(get_env("PERIODIC_TASK_PERIOD", 24 * 60 * 60)),
        # broker url needed for the celery worker
        "broker_url": get_env("CELERY_BROKER_URL", "amqp://guest@localhost//"),
    }

    # Create and configure an instance of the Flask application.
    app = Flask(__name__, instance_relative_config=True)

    # In case the database is not defined, we create a sqlite db
    if default_config["SQLALCHEMY_DATABASE_URI"] is None:
        # default to a sqlite database in the instance folder
        db_path = os.path.join(app.instance_path, "currency_convertor.sqlite")
        default_config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        # ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

    # update the configuration of app
    app.config.update(default_config)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # initialize Flask-SQLAlchemy and the init-db command
    db.init_app(app)
    metrics.init_app(app)
    app.cli.add_command(init_db_command)

    # default handler in case the service is not found
    @app.errorhandler(404)
    def page_not_found(error):
        return {"error": "Service not found"}, 404

    # apply the blueprints to the app
    from currency_convertor import currency

    app.register_blueprint(currency.bp)

    return app


def init_db(real_data=True):
    """
    Method to initialize the database.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    Clear existing data and create new tables.
    """
    init_db()
    from currency_convertor.currency.models import ConversionRate

    res = ConversionRate.update_conversion_rates()

    click.echo("Result of database update:")
    click.echo("-------------------------------------")
    click.echo(res)
    click.echo("Initialized the database.")
