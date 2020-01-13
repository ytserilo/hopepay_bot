from telegram.messanger import *
from base.base import get_card_token, app

app.add_url_rule(
    '/6943ad10abed4fcc84998e6d7ebcf2ae201bb502b65f4109ac03f73a4c5f54d2c0d2d0ead29941769162848224eae000',
    view_func=TelegramMessanger.as_view('telegram_messanger')
)
