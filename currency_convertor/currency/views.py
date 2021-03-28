from flask import Blueprint, current_app, request

from currency_convertor import cache
from currency_convertor.currency.models import ConversionRate, allowed_currencies

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
    converted_amount = ConversionRate().convert_amount(
        from_currency, to_currency, amount, cache
    )

    if converted_amount:
        # we return the converted amount
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": float(amount),
            "converted": float(converted_amount),
        }

    # This error will appear in case of an empty database
    return error("No exchange rate was found! Please try again later!", 500)
