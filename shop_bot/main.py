from telebot import TeleBot
from bot import TGBot
from config import (TOKEN, WEBHOOK_URL, PATH, MAGAZINS)
from models.model import (User, Texts, Category, Product, Cart)
from keyboards import (START_KB, START_PAGE, START_HELLO)
from geopy.distance import geodesic
import datetime
from telebot.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Update,
                           InlineQueryResultArticle, InputTextMessageContent)
from flask import Flask, request, abort
from flask_restful import Api
from api.resources import CategoryResource, ProductResource, UserResource


app = Flask(__name__)

api = Api(app, prefix='/bot/v1')

api.add_resource(CategoryResource, '/category', '/category/<string:cat_id>')
api.add_resource(ProductResource, '/product', '/product/<string:product_id>')
api.add_resource(UserResource, '/user', '/user/<string:user_id>')


bot = TeleBot(token=TOKEN)


@app.route(f'/{PATH}', methods=['POST'])
def webhook():
    """
    Function process webhook call
    """
    if request.headers.get('content-type') == 'application/json':

        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''

    else:
        abort(403)


mess_id_clear = []

root_kb_mk = ReplyKeyboardMarkup()
buttons = [KeyboardButton(button_name) for button_name in START_KB.values()]
root_kb_mk.add(*buttons)

cats = Category.objects.filter(is_root=True)
categori_kb_inl = InlineKeyboardMarkup()
buttons = [InlineKeyboardButton(text=cat.title, callback_data='category_' + str(cat.id)) for cat in cats]
categori_kb_inl.add(*buttons)


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == START_KB['start'])
def start(message):
    if message.text == START_KB['start']:
        txt = START_PAGE
    else:
        txt = START_HELLO
    bot.send_message(message.chat.id, txt, reply_markup=root_kb_mk)

    User.upsert_user(
        telegram_id=message.from_user.id,
        username=message.from_user.first_name,
        fullname=f'{message.from_user.username} {message.from_user.last_name}'
        )


@bot.message_handler(func=lambda message: message.text == START_KB['categories'])
def categories(message):
    bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=categori_kb_inl)


@bot.message_handler(func=lambda message: message.text == START_KB['promo'])
def categories(message):
    kb = InlineKeyboardMarkup()
    for product in Product.get_promo_products():
        if int(product.discount_price) < int(product.price):
            price = f'{product.discount_price}'
        else:
            price = product.price
        button = [InlineKeyboardButton(text=f'{product.title[0:15]} Цена: {price}', callback_data=f'producttocar_{product.id}')]
        kb.add(*button)

    bot.send_message(message.chat.id,'Список акционных товаров:',reply_markup=kb)


@bot.message_handler(func=lambda message: message.text == START_KB['cabinet'])
def categories(message):
    cart = Cart.get_orders(telegram_id=str(message.from_user.id))

    for order in cart:
        products = {str(cart_product.product.id): cart_product.product for cart_product in order.get_cart_products()}
        sum_total = 0
        for id_pro, cart_pro in products.items():
            sum_total += order.get_count_product(product=cart_pro.id)*cart_pro.get_price()
            header = f'ООО "Рога и Копыта"\n г.Киев'
            date_order = order['confirmed_date'].strftime("%m/%d/%Y, %H:%M:%S")
            type_deliv = order['type_delivery']
            user_info = f'Покупатель: {order.user.username}' if order.user.phone_number is None else \
                f'Покупатель: {order.user.username}\nТел. {order.user.phone_number}'
            delimiter = '-'*40
        order_info = f'{header}\nДата: {date_order}\n{delimiter}\nСумма заказа: {sum_total}\nНДС 20%: {round(sum_total/6,2)}' \
                     f'\n{delimiter}\n{user_info}\nТип поставки: {type_deliv}'
        bot.send_message(message.chat.id, order_info, reply_markup='')


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'category')
def get_cat_or_products(call):
    kb = InlineKeyboardMarkup()
    category = Category.objects.get(id=call.data.split('_')[1])
    if category.subcategory:
        buttons = [
            InlineKeyboardButton(text=cat.title, switch_inline_query_current_chat='subcat_' + str(cat.id)
                                 ) for cat in category.subcategory]
    kb.add(*buttons)
    bot.edit_message_text(text=category.title, message_id=call.message.message_id, chat_id=call.message.chat.id,
                          reply_markup=kb)


@bot.inline_handler(func=lambda query: query.query.split('_')[0] == 'subcat')
def product_inline(query):
    category = Category.objects.get(id=query.query.split('_')[1])
    resultes = []
    for product in category.get_products():
        kb = InlineKeyboardMarkup()
        button = [InlineKeyboardButton(text=' + Добавить в корзину', callback_data=f'producttocar_{product.id}')]
        kb.add(*button)

        if int(product.discount_price) < int(product.price):
            price = f'Акционное предложение: {round((int(product.discount_price)/int(product.price)-1)*100)} % \n {product.discount_price} (Старая цена: {product.price})'
        else:
            price = product.price

        result1 = InlineQueryResultArticle(
            id=str({product.id}),
            title=f'{product.title}',
            description=f'Цена: {price}',
            thumb_url=f'{product.url_image}'.split(' ')[0],
            reply_markup=kb,
            input_message_content=InputTextMessageContent(
                parse_mode='HTML',
                disable_web_page_preview=False,
                message_text=f"<b>{product.title}</b> \n {product.description} \n <b>Цена: {price}</b><a href='{str(product.url_image).split(' ')[0]}'>&#8204</a>"
            )
        )
        resultes.append(result1)

    bot.answer_inline_query(query.id, resultes)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'producttocar')
def add_to_car(call):
    product_ = Product.objects.get(id=call.data.split('_')[1])
    cart = Cart.get_or_create_cart(user_id=call.from_user.id)
    cart.add_product_to_cart(product=product_)
    bot.answer_callback_query(call.id, text="✅ Товар добавлен в корзину")


@bot.message_handler(func=lambda message: message.text == START_KB['cart'])
def get_cart(message):

    cart = Cart.get_or_create_cart(user_id=message.from_user.id)
    if len(cart.get_cart_products()) == 0:
        bot.send_message(message.from_user.id,text='Вы еще не добавили товары в корзину',  reply_markup='')
    else:
        products = {str(cart_product.product.id): cart_product.product for cart_product in cart.get_cart_products()}
        sum_total = 0
        for id_pro, cart_pro in products.items():
            sum_total += cart.get_count_product(product=cart_pro.id)*cart_pro.get_price()
            product_desc = f"{cart_pro.title}\n" \
                           f"Кол-во {cart.get_count_product(product=cart_pro.id)} Цена: {cart_pro.get_price()}\n" \
                           f"Сумма: {cart.get_count_product(product=cart_pro.id)*cart_pro.get_price()}\n"

            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(text=u'🔻 убрать', callback_data='cartdecrease_' + str(id_pro)),
                InlineKeyboardButton(text=cart.get_count_product(product=id_pro), callback_data='---'),
                InlineKeyboardButton(text=u'🔺 добавить', callback_data='cartincrease_' + str(id_pro)),
                InlineKeyboardButton(text=u'❌ ❗ удалить товар',
                                     callback_data='cartdelete_' + str(id_pro))
            )
            bot.send_message(message.from_user.id, product_desc, reply_markup=kb)

        kb1 = InlineKeyboardMarkup(row_width=2)
        kb1.add(
            InlineKeyboardButton(text='🆑 Очистить корзину', callback_data='clear_car'),
            InlineKeyboardButton(text='💚 Оформить заказ', callback_data='confirm_order'),
        )
        bot.send_message(message.from_user.id,text='Желаете оформить заказ?',  reply_markup=kb1)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'cartincrease')
@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'cartdecrease')
def change_qty_prod(call):
    product_ = Product.objects.get(id=call.data.split('_')[1])
    cart = Cart.get_or_create_cart(user_id=call.from_user.id)
    kb = InlineKeyboardMarkup()

    if call.data.split('_')[0] == 'cartincrease':
        if product_.get_quantity()> cart.get_count_product(product=product_):
            cart.add_product_to_cart(product=product_)
            product_desc = f"{product_.title}\n" \
                           f"Кол-во {cart.get_count_product(product=product_.id)} Цена: {product_.get_price()}\n" \
                           f"Сумма: {cart.get_count_product(product=product_.id) * product_.get_price()}\n"
            kb.add(
                InlineKeyboardButton(text=u'🔻 убрать', callback_data='cartdecrease_' + str(product_.id)),
                InlineKeyboardButton(text=cart.get_count_product(product=product_.id), callback_data='---'),
                InlineKeyboardButton(text=u'🔺 добавить', callback_data='cartincrease_' + str(product_.id)),
                InlineKeyboardButton(text=u'❌ ❗ удалить товар',
                                     callback_data='cartdelete_' + str(product_.id))
            )
            bot.edit_message_text(text=product_desc, chat_id=call.from_user.id, message_id=call.message.message_id)
            bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=kb)
        else:
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text='Извините, это максимальное кол-во товара которое есть на остатке.')
    elif call.data.split('_')[0] == 'cartdecrease':
        cart.decrease_qty_product_cart(product=product_.id)
        product_desc = f"{product_.title}\n" \
                       f"Кол-во {cart.get_count_product(product=product_.id)} Цена: {product_.get_price()}\n" \
                       f"Сумма: {cart.get_count_product(product=product_.id) * product_.get_price()}\n"
        kb.add(
            InlineKeyboardButton(text=u'🔻 убрать', callback_data='cartdecrease_' + str(product_.id)),
            InlineKeyboardButton(text=cart.get_count_product(product=product_.id), callback_data='---'),
            InlineKeyboardButton(text=u'🔺 добавить', callback_data='cartincrease_' + str(product_.id)),
            InlineKeyboardButton(text=u'❌ ❗ удалить товар',
                                 callback_data='cartdelete_' + str(product_.id))
        )
        bot.edit_message_text(text=product_desc, chat_id=call.from_user.id, message_id=call.message.message_id)
        bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=kb)

        if cart.get_count_product(product=product_.id) == 0 and len(cart.get_cart_products()) > 0:
            cart.delete_product_from_cart(product=product_)
            bot.edit_message_text(text='Товар удален с корзины', chat_id=call.from_user.id, message_id=call.message.message_id)

        elif cart.get_count_product(product=product_.id) == 0 > 0:
            product_desc = f"{product_.title}\n" \
                           f"Кол-во {cart.get_count_product(product=product_.id)} Цена: {product_.get_price()}\n" \
                           f"Сумма: {cart.get_count_product(product=product_.id) * product_.get_price()}\n"
            kb.add(
                InlineKeyboardButton(text=u'🔻 убрать', callback_data='cartdecrease_' + str(product_.id)),
                InlineKeyboardButton(text=cart.get_count_product(product=product_.id), callback_data='---'),
                InlineKeyboardButton(text=u'🔺 добавить', callback_data='cartincrease_' + str(product_.id)),
                InlineKeyboardButton(text=u'❌ ❗ удалить товар',
                                     callback_data='cartdelete_' + str(product_.id))
            )
            bot.edit_message_text(text=product_desc, chat_id=call.from_user.id, message_id=call.message.message_id)
            bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=kb)

        elif len(cart.get_cart_products()) == 0:
            Cart.clear_cart(cart)
            bot.answer_callback_query(call.id, show_alert=True, text="💔 Корзина очищена")
            bot.send_message(call.from_user.id, START_PAGE, reply_markup=root_kb_mk)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'cartdelete')
def change_qty_prod(call):
    product_ = Product.objects.get(id=call.data.split('_')[1])
    cart = Cart.get_or_create_cart(user_id=call.from_user.id)
    cart.delete_product_from_cart(product=product_)
    bot.edit_message_text(text='Товар удален с корзины', chat_id=call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'clear')
def order_clear(call):
    cart = Cart.get_or_create_cart(call.from_user.id)
    Cart.clear_cart(cart)
    bot.answer_callback_query(call.id, show_alert=True, text="💔 Корзина очищена")
    bot.send_message(call.from_user.id, START_PAGE, reply_markup=root_kb_mk)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'confirm')
def order_confirm(call):
    cart = Cart.get_or_create_cart(user_id=call.from_user.id)
    # cart_prod =
    if len(cart.get_cart_products()) == 0:
        bot.send_message(call.from_user.id,text='Вы еще не добавили товары в корзину',  reply_markup='')
    else:
        products = {str(cart_product.product.id): cart_product.product for cart_product in cart.get_cart_products()}
        sum_total = 0
        for id_pro, cart_pro in products.items():
            sum_total += cart.get_count_product(product=cart_pro.id) * cart_pro.get_price()
            header = f'ООО "Рога и Копыта"\n г.Киев'
            user_info = f'Покупатель: {cart.user.username}' if cart.user.phone_number is None else \
                f'Покупатель: {cart.user.username}\nТел. {cart.user.phone_number}'
            delimiter = '-' * 40
            order_info = f'{header}\n{delimiter}\nСумма заказа: {sum_total}\n' \
                         f'НДС 20%: {round(sum_total/6,2)}\n{delimiter}\n{user_info}'
        bot.send_message(call.from_user.id, order_info, reply_markup='')

        orders_menu = ReplyKeyboardMarkup(row_width=2)
        orders_menu.add(
            KeyboardButton(text='🗺️ Самовывоз - ближайший магазин', request_location=True),
            KeyboardButton(text='☎ Адресная доставка', request_contact=True),
            KeyboardButton(text=START_KB['start'])
            )
        bot.send_message(call.from_user.id, text=f'Выберите способ получения заказа', reply_markup=orders_menu)


@bot.message_handler(func=lambda message: True, content_types=['location'])
def user_location(message):
    lon = message.location.longitude
    lat = message.location.latitude

    distance = []
    for m in MAGAZINS:
        rezult = geodesic((m['latm'], m['lonm']), (lat, lon)).kilometers
        distance.append(rezult)
    index = distance.index(min(distance))
    bot.send_message(message.chat.id, text='Ближайший к Вам магазин')
    bot.send_venue(message.chat.id, MAGAZINS[index]['latm'], MAGAZINS[index]['lonm'],
                MAGAZINS[index]['title'], MAGAZINS[index]['adress'])

    cart = Cart.get_cart(message.from_user.id)
    cart.confirmed_cart(is_archived=True, type_delivery='Самовывоз', confirmed_date=datetime.datetime.now())
    bot.send_message(message.from_user.id, text=f"Ждем Вас в нашем магазине по адресу:\n{MAGAZINS[index]['adress']}", reply_markup=root_kb_mk)

@bot.message_handler(func=lambda message: True, content_types=['contact'])
def user_contact(message):
    phone_usr = message.contact.phone_number
    User.upsert_user(
        telegram_id=message.from_user.id,
        phone_number=phone_usr
        )

    cart = Cart.get_cart(message.from_user.id)
    cart.confirmed_cart(is_archived=True, type_delivery='Адресная доставка', confirmed_date=datetime.datetime.now())
    bot.send_message(message.from_user.id, text=f"В ближайшее время с Вами свяжется наш менеджер для принятия заказа", reply_markup=root_kb_mk)



"""
WEBHOOK_HOST = https://33.46.32.19:8443    ----https://serverdomain.com
SELF_SIGNED = 
PKEM = '/home/sertifivcatewebhook_pkem.pem'
PKEY =  '/home/sertifivcatewebhook_pkey.pem'

bot.set_webhook(WEBHOOK_HOST,open('r',PKEM))
"""
if __name__ == '__main__':
    import time
    print('Started!')
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=WEBHOOK_URL,
                    certificate=open('nginx-selfsigned.crt', 'r')
                    )
    app.run(host='127.0.0.1', port=5000, debug=True)
