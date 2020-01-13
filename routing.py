from telegram.messanger import *
from base.base import get_card_token, app

app.add_url_rule(
    '/<secret key>',
    view_func=TelegramMessanger.as_view('telegram_messanger')
)
