from liqpay import LiqPay
from abc import ABC, abstractmethod
import re, uuid, redis, json, requests, os
from flask import request, render_template, Flask, redirect
from flask_sslify import SSLify
from telegram.message_controller import MessageController
from .postal_manager import *


new_link = "your link"

app = Flask(__name__, template_folder='templates')
sslify = SSLify(app)

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost')
redis_storage = redis.from_url(redis_url)


public_key = "key"
private_key = "key"

class BaseMassanger(ABC):
    def get_orders(self, user_id, mode):
        data = redis_storage.get("orders")
        if data == None:
            redis_storage.set("orders", json.dumps({}))
            data = {}
        else:
            data = json.loads(data)

        orders = []

        for key in data:
            if data[key][mode] == user_id:
                orders.append({key: data[key]})

        return orders


    def create_test_pay(self, user_id):
        liqpay = LiqPay(
            public_key,
            private_key
        )
        unique = self.validate_id()
        html = liqpay.cnb_form({
            "action"         : "pay",
            "amount"         : "1",
            "currency"       : "UAH",
            "order_id"       : unique,
            "description"    : user_id,
            "version"        : "3",
            "server_url"     : "{}/auth_card".format(new_link),
            "result_url"     : "https://web.telegram.org/#/im?p=@HopePay_bot"
        })
        return html

    def validate_id(self):
        while True:
            unique = re.sub(r'-', '', str(uuid.uuid4()))[0:-5]
            data = redis_storage.get("orders")

            if data == None:
                redis_storage.set("orders", json.dumps({}))
                data = {}
            else:
                data = json.loads(data)

            try:
                id = data[unique]
            except:
                return unique


class PostalManager:
    async def create_invoice(self):
        pass

    async def get_info(self):
        pass

class PayView(BaseMassanger):
    pass

@app.route("/hold/<id>", methods=["GET", "POST"])
def hold(id):
    if request.method == "GET":
        storage = redis_storage.get(id)

        if storage == None:
            return render_template('index.html', error="Критическая ошыбка")
        else:
            liqpay = LiqPay(
                public_key,
                private_key
            )
            storage = json.loads(storage)

            hold = json.loads(redis_storage.get("orders"))
            hold = hold[storage['id']]
            try:
                html = liqpay.cnb_form({
                    "action"         : "hold",
                    "amount"         : hold["price"],
                    "currency"       : "UAH",
                    "description"    : storage["id"],
                    "order_id"       : str(uuid.uuid4()) + str(uuid.uuid4()),
                    "version"        : "3",
                    "server_url"     : new_link+"/hold/{}".format(id),
                    "result_url"     : "https://web.telegram.org/#/im?p=@HopePay_bot"
                })
                return render_template('index.html', html=html)
            except:
                return render_template('index.html', error="Критическая ошыбка")

    elif request.method == "POST":
        liqpay = LiqPay(public_key, private_key)

        data = request.form.get("data")

        response = liqpay.decode_data_from_str(data)

        order_id = response["description"]
        orders = json.loads(redis_storage.get("orders"))

        try:
            orders[order_id]["liqay-id"] = response["order_id"]
            orders[order_id]["payed"] = True

            message_controller = MessageController()

            redis_storage.set("orders", json.dumps(orders))

            seller_info = json.loads(redis_storage.get(orders[order_id]["seller"]))
            customer_info = json.loads(redis_storage.get(orders[order_id]["customer"]))

            message_controller.send_message(
                id=orders[order_id]["customer"],
                text="Вы успешно оплатили товар {}".format(orders[order_id]["title"])
            )
            message_controller.send_message(
                id=orders[order_id]["seller"],
                text="Покупатель успешно оплатил товар {}".format(orders[order_id]["title"])
            )

            return "OK"

        except:
            return "OK"

def search(self, data):
    value = data.get("value")
    street_mode = data.get("street_mode")
    street_value = data.get("street_value")

    return_data = None
    if street_mode:
        if len(street_value) == 0:
            return_data = find_town(value)
        else:
            return_data = find_street(value, street_value)
    else:
        return_data = find_wirehouse(value)
    return return_data

@app.route("/auth_card", methods=["GET", "POST"])
def get_card_token():
    if request.method == "GET":
        data = request.args
        id = data.get("id")

        redis_data = redis_storage.get(id)
        if redis_data == None:
            return render_template('index.html', error="Критическая ошыбка")
        else:
            redis_data = json.loads(redis_data)

            pay = PayView()
            html = pay.create_test_pay("{} {}".format(redis_data["user_id"], id))

            return render_template('index.html', html=html)

    elif request.method == "POST":
        liqpay = LiqPay(public_key, private_key)

        data = request.form.get("data")

        response = liqpay.decode_data_from_str(data)

        user_id = response["description"].split(' ')

        user_info = json.loads(redis_storage.get(user_id[0]))
        redis_storage.delete("{}".format(user_id[1]))
        try:
            user_info["last-message"]["ivent-map"]["card_token"] = response["card_token"]
        except:
            user_info["last-message"]["ivent-map"]["card_token"] = response["sender_phone"]


        redis_storage.set(user_id[0], json.dumps(user_info))

        link = "https://api.telegram.org/<bot key>/sendMessage"
        data = {
            "text": "Будь ласка відправте назву товара",
            "chat_id": user_id[0]
        }
        response = requests.post(link, json=data)

        response_data = json.loads(response.text)

        return "OKEY"
