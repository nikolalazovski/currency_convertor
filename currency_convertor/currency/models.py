import datetime
import traceback
from decimal import Decimal

import requests
from flask import current_app
from flask_sqlalchemy.model import DefaultMeta

from currency_convertor import db

# Allowed currencies into the system
# TODO: These currencies can be defined through an ENV variable
allowed_currencies = ("CZK", "EUR", "USD", "PLN")

BaseModel: DefaultMeta = db.Model


class ConversionRate(BaseModel):
    """
    ConversionRate class used as an ORM class

    Parameters
    ----------
    id : integer, auto increment
        The ID of the record
    from_currency : string
        The origin currency to be converted
    to_currency : string
        The target currency
    rate : Decimal
        Instead of float, we use Numeric field in the database
        which is more suitable for financial calculation.
        In python this field is delivered as decimal.Decimal
    latest : integer
        This is an indicator whether the conversion rate is the latest or not
        1 - latest conversion rate, official
        2 - latest conversion rate, not official
        0 - conversion rate history
    created : datetime
        The datetime of creation.
        Delivered in python as datetime.datetime
    """

    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(3), nullable=False, index=True)
    to_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Numeric(12, 6), nullable=False)
    latest = db.Column(db.Integer, nullable=False, default=2)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        """
        Representation of an ConversionRate object.
        """
        return "<ConversionRate(from_currency='{}', to_currency='{}', rate={}, latest={})>".format(
            self.from_currency, self.to_currency, self.rate, self.latest
        )

    def convert_amount(self, from_currency, to_currency, amount, cache=None):
        cache_key = f"{from_currency}_{to_currency}"
        rate = cache.get(cache_key) if cache is not None else None

        if rate:
            return ConversionRate.financial_multiplication(amount, rate)

        # if no cached value is found,
        # we read the valid value from the database and set the cache
        exchange_rate = self.query.filter_by(
            from_currency=from_currency, to_currency=to_currency, latest=1
        ).first()

        rate = exchange_rate.rate if exchange_rate else None

        if cache and rate:
            # the cache is set depending on the PERIODIC_TASK_PERIOD
            # that defines the celery cycle for reading the new
            # exchange rates
            delta = datetime.timedelta(
                seconds=current_app.config["PERIODIC_TASK_PERIOD"]
            )
            # the cache is valid until TIME IT WAS CREATED + PERIODIC_TASK_PERIOD
            expiry_time = int((exchange_rate.created + delta).timestamp())
            cache.set(cache_key, rate, expiry_time)

        return (
            ConversionRate.financial_multiplication(amount, rate)
            if rate is not None
            else None
        )

    @staticmethod
    def financial_multiplication(a, b):
        """
        Financial multiplication using the decimal.Decimal class
        instead of python's float data type.
        Input values are converted to string and then casted by
        decimal.Decimal class.

        Parameters
        ----------
        a : float | string | decimal.Decimal
            First multiplier.
        b : float | string | decimal.Decimal
            Second multiplier.

        Returns
        -------
        decimal.Decimal
        """
        if not isinstance(a, Decimal):
            a = Decimal(str(a))
        if not isinstance(b, Decimal):
            b = Decimal(str(b))

        return a * b

    @staticmethod
    def get_conversion_rate(curr1, curr2):
        """
        Method to get the exchange rate through the API service.

        Parameters
        ----------
        curr1 : string
            Origin currency
        curr2 : float | string | decimal.Decimal
            Destination currency

        Returns
        -------
        float

        Raises
        ------
        requests.exceptions.RequestException
        """

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

    @staticmethod
    def update_conversion_rates():
        """
        Main method to update the conversion rates.
        """

        conversion_rates = {}
        try:
            # reading all exchange rates
            # because there is no bulk request
            # we read each exchange rate in a separate API call
            for c1 in allowed_currencies:
                for c2 in allowed_currencies:
                    rate = str(ConversionRate.get_conversion_rate(c1, c2))
                    new_rate = ConversionRate(
                        from_currency=c1, to_currency=c2, rate=rate
                    )
                    # writing the new rates into the database with latest = 2
                    db.session.add(new_rate)
                    conversion_rates[f"{c1}_{c2}"] = rate

            # making the newest rates as official and the old ones going to history
            db.session.query(ConversionRate).filter(ConversionRate.latest > 0).update(
                {"latest": (ConversionRate.latest - 1)}
            )
            # commiting the changes into the database
            db.session.commit()
        except Exception as e:
            # in case something goes wrong we rollback => the old excahnge rates will be used
            # TODO: Send mail to the admins as a notification for failed reading of exchange rates
            db.session.rollback()
            return {
                "success": 0,
                "error": str(traceback.format_exc()),
                "data": conversion_rates,
            }

        # return all conversion rates
        return {"success": 1, "data": conversion_rates}


# creating an composite index over the data that are usually quieried
db.Index(
    "idx_current_conversion_rate",
    ConversionRate.from_currency,
    ConversionRate.to_currency,
    ConversionRate.latest,
)
