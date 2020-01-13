from base.base import BaseMassanger, redis_storage
from flask.views import View
from flask import request
from .order_manager import OrderManager
from base.postal_manager import find_wirehouse
from .message_controller import MessageController
from base.base import new_link
import requests, json, re, uuid

class TelegramUtils(View, BaseMassanger):
    def main_controller(self, data):
        try:
            self.customer_place(data)
            return "OK"
        except:
            pass
        try:
            self.customer_confirm(data)
            return "OK"
        except:
            pass
        try:
            self.enter_full_name(data["message"]["text"], data["message"]["chat"]["id"])
            return "OK"
        except:
            pass
        try:
            photo = data["message"]["photo"]
            self.edit_controller(photo, data["message"]["chat"]["id"])
            return "OK"
        except:
            try:
                self.edit_controller(data["message"]["text"], data["message"]["chat"]["id"])
                return "OK"
            except:
                pass
        try:
            photo = data["message"]["photo"]
            self.message_controller(photo, data["message"]["chat"]["id"])
            return "OK"
        except:
            try:
                self.message_controller(data["message"]["text"], data["message"]["chat"]["id"])
                return "OK"
            except:
                pass

        try:
            if data["callback_query"]["data"] == "cencell":
                self.cencell_edit(data["callback_query"]["message"]["chat"]["id"])
                return "OK"
            elif data["callback_query"]["data"] == "cencell-offer-code":
                user_data = json.loads(redis_storage.get(data["callback_query"]["message"]["chat"]["id"]))
                user_data["offer-code"] = {}
                del user_data["offer-code"]

                redis_storage.set(data["callback_query"]["message"]["chat"]["id"], json.dumps(user_data))
                return "OK"
            elif data["callback_query"]["data"] == "cencell-customer-to":
                user_data = json.loads(redis_storage.get(data["callback_query"]["message"]["chat"]["id"]))
                user_data["customer-to"] = {}
                del user_data["customer-to"]

                redis_storage.set(data["callback_query"]["message"]["chat"]["id"], json.dumps(user_data))
                return "OK"
            else:
                order_manager = OrderManager()
                order_manager.order_manager(
                    data["callback_query"]["data"],
                    data["callback_query"]["message"]["chat"]["id"],
                    data["callback_query"]["message"]["message_id"]
                )
                return "OK"
        except:
            pass

        try:
            self.update_message(
                data["callback_query"]["message"]["message_id"],
                data["callback_query"]["data"],
                data["callback_query"]["message"]["chat"]["id"]
            )
            return "OK"
        except:
            pass

        return "OK"

    def customer_place(self, data):
        user = json.loads(redis_storage.get(data["message"]["chat"]["id"]))
        if user["customer-to"]["ref"] == None:
            postal = data["message"]["text"].split(' ')
            result = find_wirehouse(postal[0], postal[1])

            if result != None:
                inline_keyboard = {"inline_keyboard": [
                    [
                        {"text": result["title"], "callback_data": "{},{}".format(result["ref"], user["customer-to"]["id"])}
                    ]
                ]}
                message_controller = MessageController()
                message_controller.send_message(
                    id=data["message"]["chat"]["id"],
                    text="Выберите",
                    reply_markup=inline_keyboard
                )
            else:
                message_controller = MessageController()
                message_controller.send_message(
                    id=data["message"]["chat"]["id"],
                    text="Такого отделения нет",
                )

    def customer_confirm(self, data):
        user = json.loads(redis_storage.get(data["message"]["chat"]["id"]))

        msg_controller = MessageController()
        if user["offer-code"] == None:
            orders = json.loads(redis_storage.get("orders"))
            try:
                info = orders[data["message"]["text"]]
            except:

                msg_controller.send_message(
                    id=data["message"]["chat"]["id"],
                    text="Такой сделки нет"
                )
                return
            if orders[data["message"]["text"]]["customer"] == None and orders[data["message"]["text"]]["seller"] != data["message"]["chat"]["id"]:
                orders[data["message"]["text"]]["customer"] = data["message"]["chat"]["id"]
            else:
                msg_controller.send_message(
                    id=data["message"]["chat"]["id"],
                    text="Такой сделки не существует"
                )
                return

            user["offer-code"] = {}
            del user["offer-code"]

            redis_storage.set(data["message"]["chat"]["id"], json.dumps(user))
            redis_storage.set("orders", json.dumps(orders))

            seller_data = json.loads(redis_storage.get(orders[data["message"]["text"]]["seller"]))

            full_name = "{} {} {}".format(
                seller_data["full_name"]["first-name"],
                seller_data["full_name"]["last-name"],
                seller_data["full_name"]["middle-name"]
            )
            full_name_customer = "{} {} {}".format(
                user["full_name"]["first-name"],
                user["full_name"]["last-name"],
                user["full_name"]["middle-name"]
            )


            msg_controller.send_message(
                id=data["message"]["chat"]["id"],
                text="Вы успешно добавлены в сделку {}\n к {}".format(
                    orders[data["message"]["text"]]["title"],
                    full_name
                )
            )
            msg_controller.send_message(
                id=orders[data["message"]["text"]]["seller"],
                text="Покупатель {} \nприсоеденился к сделке {}".format(
                    full_name_customer,
                    orders[data["message"]["text"]]["title"]
                )
            )

    def enter_full_name(self, message_text, chat_id):
        data = json.loads(redis_storage.get(chat_id))
        message_controller = MessageController()

        full_name_form = data["full_name_form"]

        if full_name_form["first-name"] == None:
            if type(message_text) == str:
                data["full_name_form"]["first-name"] = message_text
                message_controller.send_message(
                    id=chat_id,
                    text="Введите фамилию"
                )
            else:
                message_controller.send_message(
                    id=chat_id,
                    text="Введено не валидное имя"
                )
        elif full_name_form["last-name"] == None:
            if type(message_text) == str:
                data["full_name_form"]["last-name"] = message_text
                message_controller.send_message(
                    id=chat_id,
                    text="Введите ваше Отчество"
                )
            else:
                message_controller.send_message(
                    id=chat_id,
                    text="Введено не валидную фамилию"
                )
        elif full_name_form["middle-name"] == None:
            if type(message_text) == str:
                data["full_name_form"]["middle-name"] = message_text
                message_controller.send_message(
                    id=chat_id,
                    text="Введите ваш Телефон у формате +3800000000000"
                )
            else:
                message_controller.send_message(
                    id=chat_id,
                    text="Введено не валидное отчество"
                )
        elif full_name_form["telephon"] == None:
            match = re.search(r"^((\+380)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", message_text)
            if match != None and len(message_text[3: ]) == 10:

                data["full_name_form"]["telephon"] = message_text
                data["full_name"] = data["full_name_form"]
                del data["full_name_form"]
                redis_storage.set(chat_id, json.dumps(data))

                message_controller.send_message(
                    id=chat_id,
                    text="Поздравляю вы можете использовать услуги HopePay"
                )
            else:
                message_controller.send_message(
                    id=chat_id,
                    text="Введено не валидный номер телефона,\nпожалуйста введите номер телефона у формате +3800000000000"
                )

        if full_name_form["telephon"] == None:
            redis_storage.set(chat_id, json.dumps(data))

    def cencell_edit(self, chat_id):
        user_data = json.loads(redis_storage.get(chat_id))
        user_data["edit"] = {}
        del user_data["edit"]

        message_controller = MessageController()
        message_controller.send_message(
            id=chat_id,
            text="Действие отменено"
        )

        redis_storage.set(chat_id, json.dumps(user_data))

    def edit_controller(self, message, chat_id):
        user_data = json.loads(redis_storage.get(chat_id))

        edit = user_data["edit"]
        orders_info = json.loads(redis_storage.get("orders"))

        message_controller = MessageController()
        if orders_info[edit["order-id"]]["seller"] != chat_id:
            return

        if edit["type"] == "title":
            if type(message) == str:
                orders_info[edit["order-id"]]["title"] = message

                user_data["edit"] = {}
                del user_data["edit"]
                message_controller.send_message(
                    text="Заголовок успешно изменен",
                    id=chat_id,
                )
            else:
                message_controller.send_message(
                    text="Заголовок должен быть текстом",
                    id=chat_id,
                )
        elif edit["type"] == "weight":
            try:
                weight = int(message)

                if weight <= 0:
                    message_controller.send_message(
                        id=user_id,
                        text="Вес должен быть больше 0",
                    )
                else:
                    orders_info[edit["order-id"]]["weight"] = weight

                    user_data["edit"] = {}
                    del user_data["edit"]
                    message_controller.send_message(
                        id=chat_id,
                        text="Вес успешно изменен",
                    )
            except:
                message_controller.send_message(
                    id=chat_id,
                    text="Вес должен быть числом",
                )
        elif edit["type"] == "from":
            if type(message) == str:

                res = message.split(' ')

                result = find_wirehouse(res[0], res[1])
                if result == None:
                    message_controller.send_message(
                        id=chat_id,
                        text="Отделение не найдено",
                    )
                else:

                    inline_keyboard = {"inline_keyboard": [
                        [
                            {"text": result["title"], "callback_data": "{},{}".format(result["ref"], edit["order-id"])}
                        ]
                    ]}
                    message_controller.send_message(
                        id=chat_id,
                        text="Выбирете отделение",
                        reply_markup=inline_keyboard,
                    )
        elif edit["type"] == "description":
            if type(message) == str:
                orders_info[edit["order-id"]]["description"] = message

                user_data["edit"] = {}
                del user_data["edit"]
                message_controller.send_message(
                    text="Описание успешно изменено",
                    id=chat_id,
                )
            else:
                message_controller.send_message(
                    text="Описание должно быть текстом",
                    id=chat_id,
                )
        elif edit["type"] == "img":
            if type(message) == list:
                orders_info[edit["order-id"]]["img-id"] = message[-1]["file_id"]

                user_data["edit"] = {}
                del user_data["edit"]
                message_controller.send_message(
                    text="Изображение успешно изменено",
                    id=chat_id,
                )
            else:
                message_controller.send_message(
                    text="Пожалуйста отправте изображение",
                    id=chat_id,
                )
        elif edit["type"] == "price":
            try:
                price = int(message)
                orders_info[edit["order-id"]]["price"] = price

                user_data["edit"] = {}
                del user_data["edit"]
                message_controller.send_message(
                    text="Цена успешно изменена",
                    id=chat_id,
                )
            except:
                message_controller.send_message(
                    text="Цена должна быть числом",
                    id=chat_id,
                )
        redis_storage.set("orders", json.dumps(orders_info))
        redis_storage.set(chat_id, json.dumps(user_data))

    def update_message(self, id_message, message, chat_id):
        data = json.loads(redis_storage.get(chat_id))

        update_data = {
            "chat_id": chat_id,
            "message_id": id_message,
            "text": "Выберите",
        }
        if data["last-message"]["text"] == "Получить мои товары":
            try:
                message_controller = MessageController()

                page = int(message)
                inline_keyboard = self.get_inline_orders("seller", chat_id, page)
                update_data["reply_markup"] = inline_keyboard
                message_controller.send_update(update_data)
            except:
                data_redis = json.loads(redis_storage.get("orders"))
                info = data_redis[message]

                self.send_info(info, id_message, chat_id, message)

        elif data["last-message"]["text"] == "Получить мои покупки":
            try:
                message_controller = MessageController()

                page = int(message)
                inline_keyboard = self.get_inline_orders("customer", chat_id, page)
                update_data["reply_markup"] = inline_keyboard
                message_controller.send_update(update_data)
            except:
                data_redis = json.loads(redis_storage.get("orders"))
                info = data_redis[message]

                self.send_info(info, id_message, chat_id, message)

    def send_info(self, info, id_message, chat_id, message):
        id_message += 1
        photo = {
            "chat_id": chat_id,
            "media": {"type": "photo", "media": info["img-id"], "caption": "Заголовок:{0}\nОписание: {1}\nЦена: {2} UAH\nВес: {3} грам\nУникальный ID покупки для покупателя:".format(
                info["title"],
                info["description"],
                info["price"],
                info["weight"],
            )},
            "message_id": id_message,
        }
        control_keyboard = {
            "chat_id": chat_id,
            "text": "Выберите",
            "reply_markup": {"inline_keyboard": [[]]},
            "message_id": id_message+2,
        }

        if info["seller"] == chat_id:
            if info["payed"] == False:
                control_keyboard["reply_markup"]["inline_keyboard"][0].append({
                    "text": "Редактировать", "callback_data": json.dumps({
                        "type":"edit",
                        "id":message
                    })
                })
                control_keyboard["reply_markup"]["inline_keyboard"][0].append({
                    "text": "Удалить", "callback_data": json.dumps({
                        "type":"delete",
                        "id":message
                    })
                })
                if info["customer"] != None:
                    control_keyboard["reply_markup"]["inline_keyboard"][0].append({
                        "text": "Удалить покупателя", "callback_data": json.dumps({
                            "type":"del-c",
                            "id":message
                        })
                    })

        else:
            if info["to"] == None:
                control_keyboard["reply_markup"]["inline_keyboard"][0].append({
                    "text": "Ввести адрес получение", "callback_data": json.dumps({
                        "type":"to",
                        "id":message
                    })
                })
            elif info["payed"] == False:
                control_keyboard["reply_markup"]["inline_keyboard"][0].append({
                    "text": "Оплатить", "callback_data": json.dumps({
                        "type":"hold",
                        "id":message
                    })
                })
                #if click return render

        message_controller = MessageController()
        message_controller.send_or_update_message("media", photo)
        message_controller.send_or_update_message("text", {
            "chat_id": chat_id,
            "text": message,
            "message_id": id_message+1
        })
        message_controller.send_or_update_message("text", control_keyboard)
        if info["payed"] == True:
            message_controller.send_or_update_message("text", {
                "chat_id": chat_id,
                "text": "Номер накладной не доступен в тестовом режиме\n(скоро будет полноценный режим)",
                "message_id": id_message+3
            })

    def message_controller(self, message_text, user_id):
        #redis_storage.delete("orders")
        data = redis_storage.get(user_id)

        if data == None:
            redis_storage.set(user_id, json.dumps({
                "last-message": {"text": "", "ivent-map": {}},
                "card-token": None,
                "full_name_form": {
                    "telephon": None,
                    "first-name": None,
                    "last-name": None,
                    "middle-name": None
                },
            }))
            data = json.loads(redis_storage.get(user_id))
        else:
            data = json.loads(data)

        try:
            if data["last-message"]["text"] != "Получить мои покупки" and data["last-message"]["text"] != "Получить мои товары":
                data["last-message"]["text"] = message_text

                redis_storage.set(user_id, json.dumps(data))
        except:
            pass

        #"last-message": {"text": "asdasd", "ivent-map": {""}}
        try:
            self.event_map_contoller(
                data=data,
                message_text=message_text,
                user_id=user_id
            )
            return
        except:
            pass
        message_controller = MessageController()

        if message_text == "/start":
            reply_markup = {
                "keyboard": [
                    [
                        {"text": "Купить"},
                        {"text": "Продать"},
                    ],
                    [
                        {"text": "Получить мои покупки"},
                        {"text": "Получить мои товары"}
                    ]
                ],
                "resize_keyboard": True,
            }
            message_controller.send_message(
                id=user_id,
                text="Добро пожаловать",
                reply_markup=reply_markup
            )
            user_data = json.loads(redis_storage.get(user_id))
            try:
                tel = user_data["full_name"]["telephon"]
                if tel == None:
                    message_controller.send_message(
                        id=user_id,
                        text="Введите свое имя",
                    )
            except:
                message_controller.send_message(
                    id=user_id,
                    text="Введите свое имя",
                )
        elif message_text == "Продать":

            data["last-message"]["ivent-map"] = {
                "title": None,
                "description": None,
                "img-id": None,
                "price": None,
                "payed": False,
                "weight": None,
                "from": None,
                "success": False,
                "to": None,
                "card-token": None
            }
            uniq_link = None
            redis_storage.set(user_id, json.dumps(data))
            while True:
                id = str(uuid.uuid4())
                uniq_link = redis_storage.get(id)
                if uniq_link != None:
                    continue
                else:
                    uniq_link = id
                    break

            html = '<a href="'+new_link+'/auth_card?id={}">Тестова покупка для получения токена катры\nссылка доступна 5 мин.</a>'.format(uniq_link)
            redis_storage.set(uniq_link, json.dumps({
                "user_id": user_id,
            }))
            redis_storage.expire(uniq_link, 300)
            message_controller.send_message(
                id=user_id,
                text=html,
                parse_mode="HTML",
            )
        elif message_text == "Купить":

            message_controller.send_message(
                id=user_id,
                text="Пожалуйсте введите уникальный код от продавца",
                reply_markup={"inline_keyboard": [[{"text": "Отменить","callback_data":"cencell-offer-code"}]]}
            )
            user_data = json.loads(redis_storage.get(user_id))
            user_data["offer-code"] = None

            redis_storage.set(user_id, json.dumps(user_data))

        elif message_text == "Получить мои покупки":
            inline_keyboard = self.get_inline_orders(
                mode="customer",
                user_id=user_id,
                page=1
            )

            if inline_keyboard:
                message_controller.send_message(
                    id=user_id,
                    text="Выбирите",
                    reply_markup=inline_keyboard
                )
            else:
                message_controller.send_message(
                    id=user_id,
                    text="Вы не имеете покупок"
                )

        elif message_text == "Получить мои товары":
            inline_keyboard = self.get_inline_orders(
                mode="seller",
                user_id=user_id,
                page=1
            )

            if inline_keyboard:
                message_controller.send_message(
                    id=user_id,
                    text="Выбирите",
                    reply_markup=inline_keyboard
                )
            else:
                message_controller.send_message(
                    id=user_id,
                    text="Ви не имете своих товаров"
                )

    def get_inline_orders(self, mode, user_id, page):
        orders = self.get_orders(user_id, mode)

        max_pages = len(orders) // 10
        if len(orders) % 10 != 0:
            max_pages += 1

        try:
            page = int(page)
            if max_pages < page:
                page = max_pages
        except:
            page = 0
        inline_keyboard = {
            "inline_keyboard": []
        }

        counter = 0
        orders = orders[(page-1)*10: (page-1)*10+10]

        for i in range(len(orders)):
            if i % 2 == 0:
                append_list = []
                for key, value in orders[i].items():
                    append_list.append({
                        "text": orders[i][key]["title"],
                        "callback_data": key,
                    })
                try:
                    for key, value in orders[i+1].items():
                        append_list.append({
                            "text": orders[i+1][key]["title"],
                            "callback_data": key,
                        })
                    i += 1
                except:
                    pass
                inline_keyboard["inline_keyboard"].append(append_list)

        if len(inline_keyboard["inline_keyboard"]) == 0:
            return False
        else:
            nav_pages = None
            if max_pages == 1:
                pass
            elif page == 1 and max_pages > 1:
                nav_pages = [{
                    "text": ">",
                    "callback_data": page+1,
                }]
            elif page == max_pages:
                nav_pages = [{
                    "text": "<",
                    "callback_data": page-1,
                }]
            elif max_pages >= 3 and page < max_pages:
                nav_pages = [
                    {"text": "<", "callback_data": page-1},
                    {"text": ">", "callback_data": page+1}
                ]

            if nav_pages != None:
                inline_keyboard["inline_keyboard"].append(nav_pages)

            return inline_keyboard


    def event_map_contoller(self, data, message_text, user_id):
        map = data["last-message"]["ivent-map"]
        message_controller = MessageController()

        if map["card_token"] == None:
            html = self.create_test_pay(user_id)
            message_controller.send_message(
                id=user_id,
                text=html,
                parse_mode="HTML"
            )
            return
        elif map["title"] == None:
            if type(message_text) != list:
                map["title"] = message_text
                message_controller.send_message(
                    id=user_id,
                    text="Пожалуйста отправте описания товара",
                )
        elif map["description"] == None:
            if type(message_text) != list:
                map["description"] = message_text
                message_controller.send_message(
                    id=user_id,
                    text="Пожалуйста отправте изображения товара",
                )
        elif map["img-id"] == None:
            if type(message_text) == list:
                map["img-id"] = message_text[-1]["file_id"]
                message_controller.send_message(
                    id=user_id,
                    text="Пожалуйста отправте вес в грамах",
                )
        elif map["weight"] == None:
            try:
                weight = int(message_text)
                if weight <= 0:
                    message_controller.send_message(
                        id=user_id,
                        text="Вес должен быть больше 0",
                    )
                else:
                    map["weight"] = weight
                    message_controller.send_message(
                        id=user_id,
                        text="Введите место отправки у формате город пробел номер отделение",
                    )
            except:
                pass
        elif map["from"] == None:
            if type(message_text) == str:

                res = message_text.split(' ')

                result = find_wirehouse(res[0], res[1])
                if result == None:
                    message_controller.send_message(
                        id=user_id,
                        text="Отделение не найдено",
                    )
                else:

                    inline_keyboard = {"inline_keyboard": [
                        [
                            {"text": result["title"], "callback_data": json.dumps({"type":"pf","ref":result["ref"]})}
                        ]
                    ]}
                    message_controller.send_message(
                        id=user_id,
                        text="Вибирете отделение",
                        reply_markup=inline_keyboard,
                    )

        elif map["price"] == None:
            try:
                price = int(message_text)
                order_data = map

                order_data["price"] = price
                order_data["seller"] = user_id
                order_data["customer"] = None

                orders_data = json.loads(redis_storage.get("orders"))


                orders_data[self.validate_id()] = order_data
                redis_storage.set("orders", json.dumps(orders_data))
                data["last-message"]["ivent-map"] = {}
                del data["last-message"]["ivent-map"]

                redis_storage.set(user_id, json.dumps(data))

                message_controller.send_message(
                    id=user_id,
                    text="Товар создан",
                )

            except:
                message_controller.send_message(
                    id=user_id,
                    text="Цена должна быть числом",
                )

        if map["price"] == None:
            data["last-message"]["ivent-map"] = map
            redis_storage.set(user_id, json.dumps(data))
