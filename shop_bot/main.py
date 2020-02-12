# from telebot import TeleBot
from bot import TGBot
from shop_bot.config import TOKEN
from shop_bot.models.model import (Texts, Category, Product, Cart)
from shop_bot.keyboards import START_KB
from telebot.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup)


# bot = TeleBot(token=TOKEN)
bot = TGBot(token=TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    txt = 'Hello'
    kb = ReplyKeyboardMarkup()
    buttons = [KeyboardButton(button_name) for button_name in START_KB.values()]
    kb.add(*buttons)
    bot.send_message(message.chat.id, txt, reply_markup=kb)


@bot.message_handler(func=lambda message: message.text == START_KB['categories'])
def categories(message):
    cats = Category.objects.filter(is_root=True)
    kb = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text=cat.title, callback_data=str(cat.id)) for cat in cats]
    kb.add(*buttons)
    bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
# @bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'category')
def get_cat_or_products(call):
    """
    Приходит id категории
    1) Если нет предков тогда выводим продукты
    2) Если есть предки - выводим предков

    param call:
    return
    """
    # bot.send_message(call.message.chat.id, call.data)
    # TGBot.subcategory_by_products(call, subcategory_id=call.data, user_id=call.message.chat.id, text='Далее что?')
    print(call.data)
    bot.send_message(call.message.chat.id, call.data)

    kb = InlineKeyboardMarkup()
    category = Category.objects.get(id=call.data)

    if category.subcategory: #'category_' +
        buttons = [
            InlineKeyboardButton(text=cat.title, callback_data=str(cat.id)) for cat in category.subcategory
        ]
    else: #'product_' +
        buttons = [
            InlineKeyboardButton(text=product.title, callback_data=str(product.id)) for product in category.get_products()
        ]

    kb.add(*buttons)
    bot.edit_message_text(category.title, message_id=call.message.message_id, chat_id=call.message.chat.id, reply_markup=kb)



@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'product')
def add_to_car(call):
    product_id = call.data.split('_')[1]
    cart = Cart.get_or_create_cart(user_id=call.message.chat.id)
    cart.add_product_to_cart(product_id=product_id)





"""
WEBHOOK_HOST = https://33.46.32.19:8443    ----https://serverdomain.com
SELF_SIGNED = 
PKEM = '/home/sertifivcatewebhook_pkem.pem'
PKEY =  '/home/sertifivcatewebhook_pkey.pem'

bot.set_webhook(WEBHOOK_HOST,open('r',PKEM))




"""
# if __name__ == '__main__':
bot.polling()

