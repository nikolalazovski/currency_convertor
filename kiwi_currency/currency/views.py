import datetime

from flask import Blueprint, current_app, request

from kiwi_currency import cache
from kiwi_currency.currency.models import (
    ConversionRate,
    allowed_currencies,
    financial_multiplication,
)

bp = Blueprint("currency", __name__)


def error(message, status_code):
    """
    Error response formatter
    """
    return {"error": message}, status_code


@bp.route("/", methods=["GET"])
def index():
    """Show all available cutrrencies"""
    return {"data": list(allowed_currencies)}


@bp.route(
    "/convert/<string:from_currency>/<string:to_currency>/<string:amount>",
    methods=["GET"],
)
def convert(from_currency, to_currency, amount):
    """
    Main method in case of usage of conversion service.
    The format is:
    /convert/<string:from_currency>/<string:to_currency>/<amount>

    Parameters
    ----------
    from_currency : string
        The origin currency
    to_currency : string
        The destination currency
    amout : string
    """
    # check if the amount can be converted to float
    try:
        float(amount)
    except ValueError:
        return error("The amount has to be numeric", 400)

    # check if the currencies are one of the allowed
    if from_currency not in allowed_currencies:
        return error(
            "The origin currency {} is not found! Allowed currencies: {}".format(
                from_currency, ",".join(allowed_currencies)
            ),
            400,
        )

    if to_currency not in allowed_currencies:
        return error(
            "The destination currency {} is not found! Allowed currencies: {}".format(
                to_currency, ",".join(allowed_currencies)
            ),
            400,
        )

    # checking the in-memory cache for stored values that are not expired
    cache_key = f"{from_currency}_{to_currency}"
    rate = cache.get(cache_key)

    if rate is None:
        # if no cached value is found,
        # we read the valid value from the database and set the cache
        exchange_rate = ConversionRate.query.filter_by(
            from_currency=from_currency, to_currency=to_currency, latest=1
        ).first()

        if exchange_rate:
            rate = exchange_rate.rate
            # the cache is set depending on the PERIODIC_TASK_PERIOD
            # that defines the celery cycle for reading the new
            # exchange rates
            delta = datetime.timedelta(
                seconds=current_app.config["PERIODIC_TASK_PERIOD"]
            )
            # the cache is valid until TIME IT WAS CREATED + PERIODIC_TASK_PERIOD
            expiry_time = int((exchange_rate.created + delta).timestamp())
            cache.set(cache_key, rate, expiry_time)

    if rate:
        # we return the converted amount
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": float(amount),
            "converted": float(financial_multiplication(amount, rate)),
        }

    # This error will appear in case of an empty database
    return error("No exchange rate was found! Please try again later!", 500)
