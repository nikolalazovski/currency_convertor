import json
import os
from datetime import datetime
from decimal import Decimal

import requests

import boto3
from boto3.dynamodb.conditions import Key

currency_api_id = os.getenv("CURRENCY_API_ID", "")
currency_api_query_template = (
    "https://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}"
)

table_name = "conversion_rate"
allowed_currencies = ["USD", "EUR", "PLN", "CZK"]


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)


def response(data, code=200):
    if code == 200:
        return {
            "statusCode": 200,
            "body": json.dumps(data),
        }
    else:
        return {
            "statusCode": code,
            "body": json.dumps({"error": data}),
        }


def financial_multiplication(a, b):
    return Decimal(str(a)) * Decimal(str(b))


def query_conversion_rates(currency1, currency2):

    conversion_pair = f"{currency1}_{currency2}"
    response = table.query(
        KeyConditionExpression=Key("conversion_pair").eq(conversion_pair),
        ScanIndexForward=False,
    )
    return response["Items"]


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    path_parameters = event.get("pathParameters", {})

    from_currency = path_parameters.get("from_currency", "")
    to_currency = path_parameters.get("to_currency", "")
    amount = path_parameters.get("amount", "")

    # ------------------------------------------------------------------
    # validation -------------------------------------------------------

    try:
        float(amount)
    except:
        return response("The amount has to be numeric!", 400)

    if from_currency not in allowed_currencies:
        return response("The origin currency is not allowed!", 400)

    if to_currency not in allowed_currencies:
        return response("The destination currency is not allowed!", 400)

    # END validation ----------------------------------------------------
    # -------------------------------------------------------------------

    rate_items = query_conversion_rates(from_currency, to_currency)
    rate = Decimal(rate_items[0]["rate"] if rate_items else "1.20")

    return response(
        {
            "converted": float(financial_multiplication(amount, rate)),
            "amount": float(amount),
            "from_currency": from_currency,
            "to_currency": to_currency,
        }
    )


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
        query = currency_api_query_template.format(curr1, curr2, currency_api_id)
        response = requests.get(query, timeout=5.0)
        data = response.json()

        return data[f"{curr1}_{curr2}"]
    except requests.exceptions.RequestException as e:
        raise e


def lambda_handler_task(event, context):
    """
    Main lambda method to update the conversion rates.
    """

    conversion_rates = {}
    try:
        # reading all exchange rates
        # because there is no bulk request
        # we read each exchange rate in a separate API call
        for c1 in allowed_currencies:
            for c2 in allowed_currencies:
                rate = str(get_conversion_rate(c1, c2))
                # new_rate = ConversionRate(from_currency=c1, to_currency=c2, rate=rate)
                # # writing the new rates into the database with latest = 2
                # db.session.add(new_rate)
                table.put_item(
                    Item={
                        "conversion_pair": f"{c1}_{c2}",
                        "created": str(datetime.utcnow()),
                        "rate": rate,
                    }
                )
                conversion_rates[f"{c1}_{c2}"] = rate

    except Exception as e:
        # in case something goes wrong we rollback => the old excahnge rates will be used
        # TODO: Send SNS message to admin in case some of the requests/db fail
        return {
            "success": 0,
            "error": str(e),
            "data": conversion_rates,
        }

    # return all conversion rates
    return {"success": 1, "data": conversion_rates}
