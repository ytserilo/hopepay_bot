from base.base import redis_storage
from base.base import new_link
from .message_controller import MessageController
import json, re, uuid

class OrderManager:
    def order_manager(self, message_text, chat_id, message_id):

        try:
            message = message_text.split(',')
            data = json.loads(redis_storage.get("orders"))
            if data[message[1]]["customer"] == chat_id:
                data[message[1]]["to"] = message[0]
                text = "Место получение установлено, оплатите товар"

                usr_data = json.loads(redis_storage.get(chat_id))
                del usr_data["customer-to"]
                redis_storage.set(chat_id, json.dumps(usr_data))
            else:
                data[message[1]]["from"] = message[0]
                text = "Место отправки установлено"

            redis_storage.set("orders", json.dumps(data))
            message_controller = MessageController()

            message_controller.send_message(
                id=chat_id,
                text=text
            )
            return
        except:
            message_text = json.loads(message_text)

        orders = json.loads(redis_storage.get("orders"))

        if message_text["type"] == "pf":
            user = json.loads(redis_storage.get(chat_id))
            user["last-message"]["ivent-map"]["from"] = message_text["ref"]

            redis_storage.set(chat_id, json.dumps(user))
            message_controller = MessageController()
            message_controller.send_message(
                id=chat_id,
                text="Установите цену"
            )
        elif message_text["type"] == "to":
            self.customer_place(chat_id, message_text["id"])

        elif message_text["type"] == "hold":
            id = None
            while True:
                id = str(uuid.uuid4())
                store = redis_storage.get(id)
                if store != None:
                    continue
                else:
                    break

            redis_storage.set(id, json.dumps({"id": message_text["id"]}))
            redis_storage.expire(id, 300)
            html = "<a href='{}'>Нажмите для заморозки счета нажмите</a>".format(
                new_link+"/hold/{}".format(id)
            )
            message_controller = MessageController()
            message_controller.send_message(
                id=chat_id,
                text=html,
                parse_mode="HTML",
            )


        elif message_text["type"] == "delete":
            self.delete_order(message_text["id"], chat_id, message_id)

        elif message_text["type"] == "edit":
            self.edit_order(message_text["id"], chat_id, message_id)

        elif message_text["type"] == "del-c":
            self.delete_customer(message_text["id"], chat_id, message_id)

        elif message_text["type"] in ["title", "desc", "img", "price", "from", "weight"]:
            self.edit(
                message_text["id"],
                chat_id,
                message_id,
                message_text["type"]
            )

    def customer_place(self, user_id, order_id):
        data = json.loads(redis_storage.get(user_id))
        data["customer-to"] = {"ref": None, "id": order_id}
        redis_storage.set(user_id, json.dumps(data))
        message_controller = MessageController()

        message_controller.send_message(
            id=user_id,
            text="Введите место отправки у формате город пробел номер отделение",
            reply_markup={"inline_keyboard": [[{"text": "Отменить", "callback_data": "cencell-customer-to"}]]}
        )


    def edit(self, order_id, chat_id, message_id, type):
        user_info = json.loads(redis_storage.get(chat_id))
        orders = json.loads(redis_storage.get("orders"))
        message_controller = MessageController()

        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "отменить", "callback_data": "cencell"}]
            ]
        }
        if orders[order_id]["seller"] == chat_id:
            if type == "weight":
                user_info["edit"] = {"type": "weight", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправте новое значение масы в грамах"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )
            elif type == "from":
                user_info["edit"] = {"type": "from", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправте название города и номер отделение, пример 'Киев 1'"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )
            elif type == "title":
                user_info["edit"] = {"type": "title", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправить новый заголовок \nили нажмите"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )

            elif type == "desc":
                user_info["edit"] = {"type": "description", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправить новое описание \n или нажмите"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )

            elif type == "img":
                user_info["edit"] = {"type": "img", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправить новое изображение \n или нажмите"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )

            elif type == "price":
                user_info["edit"] = {"type": "price", "order-id": order_id}
                redis_storage.set(chat_id, json.dumps(user_info))

                text = "Отправить новую цену \n или нажмите"
                message_controller.send_message(
                    text=text,
                    id=chat_id,
                    reply_markup=inline_keyboard
                )

    def postal(self, order_id, chat_id, message_id):
        user_info = json.loads(redis_storage.get(chat_id))
        orders = json.loads(redis_storage.get("orders"))
        message_controller = MessageController()

        try:
            order = orders[order_id]
            if order["seller"] == chat_id:
                if order["payed"] == True:
                    user_info["postal-code"] = None
                    redis_storage.set(chat_id, json.dumps(user_info))

                    data = {
                        "text": "Send new postal code",
                        "chat_id": chat_id,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
                else:
                    message_controller.send_message(
                        text="You can send order postal after, when customer pay",
                        id=chat_id,
                    )
                    data = {
                        "text": "You can send order postal after, when customer pay",
                        "chat_id": chat_id,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
        except:
            pass

    def edit_order(self, order_id, chat_id, message_id):
        orders = json.loads(redis_storage.get("orders"))
        message_controller = MessageController()

        try:
            order = orders[order_id]
            if order["seller"] == chat_id:
                if order["payed"] == True:
                    data = {
                        "text": "Вы не можете редактировать заказ, потому что клиент заплатил",
                        "chat_id": chat_id,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
                else:
                    edit_array = ["title", "desc", "img", "price", "weight", "from"]
                    name_array = {
                        "title": "заголовок", "desc": "описание", "img": "изображение",
                        "price": "цена", "weight": "вес", "from": "место отправки"
                    }
                    edit_buttons = []

                    for i in edit_array:

                        edit_buttons.append([{
                            "text":"Редактировать {}".format(name_array[i]),
                            "callback_data":json.dumps({"type":i,"id":order_id})
                        }])
                    data = {
                        "text": "Выберите поле для редактирования",
                        "chat_id": chat_id,
                        "reply_markup": {"inline_keyboard": edit_buttons},
                        "message_id": message_id+1,
                    }

                    message_controller.send_or_update_message("text", data)
        except:
            pass


    def delete_customer(self, order_id, chat_id, message_id):
        orders = json.loads(redis_storage.get("orders"))
        message_controller = MessageController()

        try:
            order = orders[order_id]
            if order["seller"] == chat_id:
                if order["customer"] != None and order["payed"] == False:
                    orders[order_id]["customer"] = None
                    redis_storage.set("orders", json.dumps(orders))
                    message_controller.send_message(
                        text="Order deleted",
                        id=chat_id,
                    )
                elif order["payed"] == True:
                    data = {
                        "text": "Вы не можете удалить клиента, потому что клиент оплатил заказ",
                        "chat_id": chat_id,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
                elif order["customer"] == None:
                    data = {
                        "text": "Клиент не найден",
                        "chat_id": chat_id,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
        except:
            pass

    def delete_order(self, order_id, chat_id, message_id):
        orders = json.loads(redis_storage.get("orders"))
        message_controller = MessageController()

        try:
            order = orders[order_id]
            if order["seller"] == chat_id:
                if order["payed"] == False and order["customer"] == None:
                    del orders[order_id]

                    redis_storage.set("orders", json.dumps(orders))
                    message_controller.send_message(
                        text="Товар удален",
                        id=chat_id,
                    )
                    # delete prev and prev-prev post
                elif order["payed"] == True:
                    message_controller.send__message(
                        text="Вы не можете удалить заказ, потому что клиент платит за заказ",
                        chat_id=chat_id
                    )
                elif order["customer"] != None:
                    inline_keyboard = {
                        "inline_keyboard": [
                            [{
                                "text": "удалить покупателя",
                                "callback_data": json.dumps({
                                    "type": "delete-customer",
                                    "customer-id": order["customer"],
                                    "order-id": order_id
                                })
                            }]
                        ]
                    }
                    data = {
                        "text": "Вы не можете удалить заказ, сначала удалите клиента",
                        "chat_id": chat_id,
                        "reply_markup": inline_keyboard,
                        "message_id": message_id+1,
                    }
                    message_controller.send_or_update_message("text", data)
        except:
            pass
