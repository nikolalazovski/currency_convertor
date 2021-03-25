from kiwi_currency import db
from flask import current_app
import datetime
import requests
import traceback
from decimal import Decimal

allowed_currencies = ("CZK", "EUR", "USD", "PLN")


class ConversionRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(3), nullable=False, index=True)
    to_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Numeric(12, 6), nullable=False)
    latest = db.Column(db.Integer, nullable=False, default=2)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return "<ConversionRate(from_currency='{}', to_currency='{}', rate={}, latest={})>".format(
            self.from_currency, self.to_currency, self.rate, self.latest
        )


# creating an index over the data that are usually quieried
db.Index(
    "idx_current_conversion_rate",
    ConversionRate.from_currency,
    ConversionRate.to_currency,
    ConversionRate.latest,
)


def financial_multiplication(a, b):

    if not isinstance(a, Decimal):
        a = Decimal(str(a))
    if not isinstance(b, Decimal):
        b = Decimal(str(b))

    return a * b


def get_conversion_rate(curr1, curr2):

    if curr1 == curr2:
        return 1.0

    try:
        currency_api_query_template = current_app.config["CURRENCY_APP_TEMPLATE"]
        currency_api_id = current_app.config["CURRENCY_API_ID"]

        query = currency_api_query_template.format(curr1, curr2, currency_api_id)
        response = requests.get(query, timeout=5.0)
        data = response.json()
        return data[f"{curr1}_{curr2}"]
    except requests.exceptions.RequestException as e:
        raise e


def update_conversion_rates():

    conversion_rates = {}
    try:
        for c1 in allowed_currencies:
            for c2 in allowed_currencies:
                rate = get_conversion_rate(c1, c2)
                new_rate = ConversionRate(from_currency=c1, to_currency=c2, rate=rate)
                db.session.add(new_rate)
                conversion_rates[f"{c1}_{c2}"] = rate

        db.session.query(ConversionRate).filter(ConversionRate.latest > 0).update(
            {"latest": (ConversionRate.latest - 1)}
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {
            "success": 0,
            "error": str(traceback.format_exc()),
            "data": conversion_rates,
        }

    return {"success": 1, "data": conversion_rates}
