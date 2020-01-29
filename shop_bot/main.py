from telebot import TeleBot
from shop_bot.config import TOKEN
from shop_bot.models.model import (Texts)
from shop_bot.keyboards import START_KB
from telebot.types import (ReplyKeyboardMarkup, KeyboardButton)


bot = TeleBot(token=TOKEN)

@bot.message_handler(commands='start')
def start(message):
    txt = Texts.objects.filter(
        text_type='Greatings'
    ).get()

    kb = ReplyKeyboardMarkup()
    buttons = [KeyboardButton(button_name) for button_name in START_KB.values()]
    kb.add(*buttons)

    bot.send_message(message.chat.id,
                     txt,
                     reply_markup=kb)


if __name__ == '__main__':
    bot.polling()