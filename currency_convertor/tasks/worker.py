"""
    Celery worker is started with the following command
    after we export the variables for celery configuration

        celery -A currency_convertor.tasks.worker worker --loglevel=INFO -B

    The service used to fetch the currency exchange rates is:

        https://free.currencyconverterapi.com/

"""

import os

from celery.schedules import crontab

from currency_convertor.currency.models import ConversionRate
from currency_convertor.tasks import create_celery

celery_app = create_celery()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    periodic_task_period = sender.conf.get("PERIODIC_TASK_PERIOD")

    # Executes every day at midnight
    sender.add_periodic_task(
        periodic_task_period,  # crontab(minute=0, hour=0)
        update.s(),
        name="update currencvies every day at midnight",
    )


@celery_app.task(name="update_currency_rates_in_db")
def update():
    return ConversionRate.update_conversion_rates()
