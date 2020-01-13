import requests, json

class MessageController:
    def send_or_update_message(self, mode, data):
        link = "https://api.telegram.org/bot1054709988:AAE4Ia3q24vPjo5CvkuYD5zOzY8VuV117kw/{}"
        if mode == "media":
            response = requests.post(link.format("editMessageMedia"), json=data)
        else:
            response = requests.post(link.format("editMessageText"), json=data)

        response = json.loads(response.text)

        if response["ok"] != True:
            del data["message_id"]
            if mode == "media":
                data["media"] = [data["media"]]
                response = requests.post(link.format("sendMediaGroup"), json=data)
            else:
                response = requests.post(link.format("sendMessage"), json=data)


    def send_message(self, id, text, reply_markup=None, parse_mode=None):
        data = {
            "chat_id": id,
            "text": text,
        }
        if reply_markup != None:
            data["reply_markup"] = reply_markup
        if parse_mode != None:
            data["parse_mode"] = "HTML"


        link = "https://api.telegram.org/bot1054709988:AAE4Ia3q24vPjo5CvkuYD5zOzY8VuV117kw/sendMessage"
        response = requests.post(link, json=data)
        response_data = json.loads(response.text)
        

    def send_update(self, data):
        link = "https://api.telegram.org/bot1054709988:AAE4Ia3q24vPjo5CvkuYD5zOzY8VuV117kw/editMessageText"
        response = requests.post(link, json=data)
