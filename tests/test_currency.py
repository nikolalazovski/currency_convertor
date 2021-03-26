from decimal import Decimal

import pytest
import requests

from kiwi_currency import cache, db
from kiwi_currency.currency.models import (
    ConversionRate,
    allowed_currencies,
    financial_multiplication,
    get_conversion_rate,
    update_conversion_rates,
)


def test_root_path(client, app):
    response = client.get("/")
    res_json = response.get_json()
    assert res_json["data"] == list(allowed_currencies)


def test_convert_success_float_value(client, app):
    response = client.get("/convert/EUR/USD/4.0")
    assert response.status_code == 200

    res_json = response.get_json()
    service_amount = Decimal(str(res_json.get("converted", 0.0)))

    assert res_json.get("from_currency", "") == "EUR"
    assert res_json.get("to_currency", "") == "USD"

    with app.app_context():
        record = ConversionRate.query.filter_by(
            from_currency="EUR", to_currency="USD", latest=1
        ).first()

        expected_amount = record.rate * Decimal("4.0")
        assert service_amount == expected_amount
        assert service_amount == Decimal("4.0") * Decimal("1.193481")


def test_convert_success_integer_value(client, app):
    response = client.get("/convert/PLN/CZK/10")
    assert response.status_code == 200

    res_json = response.get_json()
    service_amount = Decimal(str(res_json.get("converted", 0.0)))

    assert res_json.get("from_currency", "") == "PLN"
    assert res_json.get("to_currency", "") == "CZK"

    with app.app_context():
        record = ConversionRate.query.filter_by(
            from_currency="PLN", to_currency="CZK", latest=1
        ).first()

        expected_amount = record.rate * Decimal("10")
        assert service_amount == expected_amount
        assert service_amount == Decimal("56.69525")

    response = client.get("/convert/PLN/CZK/10")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "a,b,result",
    [
        (
            "0.000000000000000000000000000003",
            8,
            Decimal("0.000000000000000000000000000024"),
        ),
        ("2", 0.3, Decimal("0.6")),
        ("1230.36589102", 1.2, Decimal("1476.439069224")),
        (78.5, "88.24", Decimal("6926.84")),
        (78.5, Decimal("88.24"), Decimal("6926.84")),
        (Decimal("78.5"), "88.24", Decimal("6926.84")),
        (Decimal("78.5"), Decimal("88.24"), Decimal("6926.84")),
    ],
)
def test_financial_multiplication(a, b, result):
    assert financial_multiplication(a, b) == result


@pytest.mark.parametrize(
    "path,text_in_error",
    [
        ("/convert/EUR/AAA/10", "The destination currency AAA is not found"),
        ("/convert/EUR/USD/abc", "The amount has to be numeric"),
        ("/convert/BBB/PLN/2.0", "The origin currency BBB is not found"),
    ],
)
def test_wrong_currencies_and_amount(client, path, text_in_error):
    response = client.get(path)
    assert response.status_code == 400
    res_json = response.get_json()
    assert text_in_error in res_json["error"]


def test_check_conversion_rate_repr(app):
    with app.app_context():
        print(id(app))
        obj_repr = repr(
            ConversionRate.query.filter_by(
                from_currency="PLN", to_currency="CZK", latest=1
            ).first()
        )
        assert (
            "<ConversionRate(from_currency='PLN', to_currency='CZK', rate=5.669525, latest=1)>"
            == obj_repr
        )


def test_empty_database_response(client, app):
    with app.app_context():
        db.session.query(ConversionRate).delete()
        db.session.commit()

        response = client.get("/convert/EUR/USD/4.0")
        res_json = response.get_json()

        assert response.status_code == 500
        assert "No exchange rate was found" in res_json["error"]


def test_non_existent_service(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    res_json = response.get_json()
    assert "Service not found" == res_json["error"]


def test_conversion_rate_equal_currencies():
    res = get_conversion_rate("USD", "USD")
    assert res == 1.0


def test_conversion_rate_different_currencies(app, monkeypatch):
    class Response:
        status_code = 200

        def json(self):
            return {"EUR_PLN": 2.36}

    def mock_requests_get_method(*args, **kwargs):
        return Response()

    with app.app_context():
        monkeypatch.setattr("requests.get", mock_requests_get_method)
        assert get_conversion_rate("EUR", "PLN") == 2.36


def test_conversion_rate_connection_error(app, monkeypatch):
    def mock_requests_get_method(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection Error Mock")

    with app.app_context():
        monkeypatch.setattr("requests.get", mock_requests_get_method)
        with pytest.raises(requests.exceptions.ConnectionError):
            get_conversion_rate("EUR", "PLN")


def test_conversion_rate_timeout(app, monkeypatch):
    def mock_requests_get_method(*args, **kwargs):
        raise requests.exceptions.ConnectTimeout("Connection Timeout")

    with app.app_context():
        monkeypatch.setattr("requests.get", mock_requests_get_method)
        with pytest.raises(requests.exceptions.ConnectTimeout):
            get_conversion_rate("EUR", "PLN")


def test_update_conversion_rates_success(app, monkeypatch):

    new_allowed_currencies = ("USD", "EUR")
    expected_rates = {"USD_USD": 1.0, "USD_EUR": 0.84, "EUR_USD": 1.19, "EUR_EUR": 1.0}

    def new_get_conversion_rate(c1, c2):
        return expected_rates[f"{c1}_{c2}"]

    with app.app_context():

        monkeypatch.setattr(
            "kiwi_currency.currency.models.allowed_currencies", new_allowed_currencies
        )
        monkeypatch.setattr(
            "kiwi_currency.currency.models.get_conversion_rate", new_get_conversion_rate
        )

        res = update_conversion_rates()
        assert res["success"] == 1
        assert res["data"] == expected_rates

        # checking the database
        db_res = ConversionRate.query.filter_by(
            from_currency="EUR", to_currency="USD", latest=1
        ).first()

        assert db_res.rate == Decimal(str(expected_rates["EUR_USD"]))


def test_update_conversion_rates_fail(app, monkeypatch):
    new_allowed_currencies = ("USD", "EUR")
    expected_rates = {"USD_USD": 1.0, "USD_EUR": 0.33, "EUR_USD": 1.77, "EUR_EUR": 1.0}

    def new_get_conversion_rate(c1, c2):

        if not (c1 == "EUR" and c2 == "EUR"):
            return expected_rates[f"{c1}_{c2}"]
        else:
            raise requests.exceptions.ConnectionError("Connection Error Mock HAHAHA")

    with app.app_context():
        # checking the database
        db_res_before = ConversionRate.query.filter_by(
            from_currency="EUR", to_currency="USD", latest=1
        ).first()

        monkeypatch.setattr(
            "kiwi_currency.currency.models.allowed_currencies", new_allowed_currencies
        )
        monkeypatch.setattr(
            "kiwi_currency.currency.models.get_conversion_rate", new_get_conversion_rate
        )

        res = update_conversion_rates()

        assert res["success"] == 0
        assert res["data"] == {"USD_USD": 1.0, "USD_EUR": 0.33, "EUR_USD": 1.77}
        assert "error" in res

        # checking the database didn't change
        db_res_after = ConversionRate.query.filter_by(
            from_currency="EUR", to_currency="USD", latest=1
        ).first()

        assert db_res_before.rate == db_res_after.rate
