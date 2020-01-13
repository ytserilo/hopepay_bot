from .telegram_utils import TelegramUtils
from flask import request


class TelegramMessanger(TelegramUtils):
    methods = ['POST']
    #{"last-message": "asd", "nav-message-id": "1231"}
    def dispatch_request(self):
        data = request.get_json()
        result = self.main_controller(data)

        return result
