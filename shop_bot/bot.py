from telebot import (TeleBot,types)
from models.model import (Category)

class TGBot(TeleBot):

    def __init__(self, token, *args):
        super().__init__(token, *args)

    def root_categories(self, user_id, text, callbeck_lockup, force_send=True):
        cats = Category.objects.filter(is_root=True)

        kb = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(text=cat.title, callback_data=f'{callbeck_lockup}_{str(cat.id)}') for cat in cats]
        kb.add(*buttons)
        if not force_send:
            return kb
        self.send_message(user_id, text, reply_markup=kb)


    def subcategory_by_products(self, subcategory_id, user_id=None, text=None,category_lockup='category',product_lockup='product', force_send=True):
        if not user_id and force_send:
        # if not (all(user_id, text)) and force_send:
            raise Exception('Exception force_send, can not by use whithout usre_id or text')

        category = Category.objects.get(id=subcategory_id)
        kb = types.InlineKeyboardMarkup()

        if category.subcategory:
            buttons = [
                types.InlineKeyboardButton(text=cat.title, callback_data=f'{category_lockup}_{str(cat.id)}') for cat in
                category.subcategory
            ]
        else:
            buttons = [
                types.InlineKeyboardButton(text=product.title, callback_data=f'{product_lockup}_{str(product.id)}') for product in
                category.get_products()
            ]

        kb.add(*buttons)
        if not force_send:
            return kb
        # self.send_message(user_id, text, reply_markup=kb)
        TGBot.edit_message_text(text=text, chat_id=user_id, reply_markup=kb)
        # self.edit_message_text(category.title, message_id=user_id, reply_markup=kb)
