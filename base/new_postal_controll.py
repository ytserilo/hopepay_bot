from .base import redis_storage
from liqpay import LiqPay
import requests, json


class NewPostal:
    def create_agent(self, data, mode):
        emitent_data = {
            "apiKey": "<new postal key>",
            "modelName": "Counterparty",
            "calledMethod": "save",
            "methodProperties": {
                "FirstName": data["full_name"]["first-name"],
                "MiddleName": data["full_name"]["middle-name"],
                "LastName": data["full_name"]["last-name"],
                "Phone": data["full_name"]["telephon"],
                "Email": "",
                "CounterpartyType": "PrivatePerson",
                "CounterpartyProperty": "Recipient"
            }
        }
        emitent_data["methodProperties"]["CounterpartyProperty"] = mode
        response = json.loads(request.post("https://api.novaposhta.ua/v2.0/json/", json=emitent_data).text)
        return response["data"][0]["Ref"]


    def monitor(self):
        orders = json.loads(redis_storage.get("orders"))

        for order in orders:
            try:
                postal_code = orders[order]["postal-code"]
                seller_card_token = orders[order]["card-token"]
                liqpay_id = orders[order]["liqpay-id"]


                data = {
                    "apiKey": "<new postal key>",
                    "modelName": "TrackingDocument",
                    "calledMethod": "getStatusDocuments",
                    "methodProperties": {
                        "Documents": [
                            {
                                "DocumentNumber": postal_code,
                            }
                        ]
                    }

                }

                if orders[order]["success"] != True:
                    
                    response = json.loads(requests.post("https://api.novaposhta.ua/v2.0/json/", json=data).text)
                    if response["data"][0]["StatusCode"] == "9":
                        self.hold_complete(
                            amount=orders[order]["amount"],
                            id=liqpay_id,
                        )
                        self.pay(
                            amount=orders[order]["amount"],
                            token=seller_card_token
                        )
            except:
                pass

    def hold_complete(self, id, amount):
        liqpay = LiqPay(public_key, private_key)
        res = liqpay.api("request", {
            "action"        : "hold_completion",
            "version"       : "3",
            "amount"        : amount*0.01,
            "order_id"      : id
        })

    def pay(self, price, token):
        liqpay = LiqPay(public_key, private_key)
        res = liqpay.api("request", {
            "action"               : "p2pcredit",
            "version"              : "3",
            "amount"               : price,
            "currency"             : "UAH",
            "description"          : "description text",
            "order_id"             : "order_id_1",
            "receiver_card_token"  : token,
        })
