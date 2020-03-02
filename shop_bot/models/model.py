from mongoengine import *
from pprint import pprint
import pandas

connect('shop_bot', 'default', host='localhost')

class User(Document):
    telegram_id = IntField(min_value=0) #StringField(max_length=32, required=True, unique=True) #StringField
    username = StringField(max_length=128)
    fullname = StringField(max_length=256)
    phone_number = StringField(max_length=20)
    email = EmailField()
    create_user = DateTimeField()

    @classmethod
    def upsert_user(cls, **kwargs):
        try:
            update_user = User.objects.get(telegram_id=kwargs['telegram_id'])
            update_user.update(**kwargs)
        except:
            cls(**kwargs).save()


class Cart(Document):
    user = ReferenceField(User)
    is_archived = BooleanField(default=False)
    type_delivery = StringField(max_length=128)
    confirmed_date = DateTimeField(required=False)

    @classmethod
    def get_or_create_cart(cls, user_id):

        try:
            user = User.objects.get(telegram_id=user_id)
        except:
            User.objects.create(telegram_id=user_id)
            user = User.objects.get(telegram_id=user_id)

        cart = cls.objects.filter(user=user, is_archived=False)

        if not cart:
            return cls.objects.create(user=user)
        return cart.get()

    @classmethod
    def get_cart(cls, user_id):
        try:
            user = User.objects.get(telegram_id=user_id)
        except:
            User.objects.create(telegram_id=user_id)
            user = User.objects.get(telegram_id=user_id)
        cart = cls.objects.filter(user=user, is_archived=False)
        return cart.get()

    def add_product_to_cart(self, product):
        CartProduct.objects.create(cart=self, product=product)
        self.save()

    def get_count_product(self, product):
        quantity = CartProduct.objects(cart=self, product=product).count()
        return quantity

    def decrease_qty_product_cart(self, product):
        if self.get_count_product(product=product) > 0:
            CartProduct.objects.filter(cart=self, product=product).first().delete()
            self.save()

    def delete_product_from_cart(self, product):
        CartProduct.objects.filter(cart=self, product=product).delete()
        self.save()

    def get_cart_products(self):
        filter_prod = CartProduct.objects.filter(cart=self)
        return filter_prod

    def confirmed_cart(self, **kwargs):
        self.update(**kwargs)

    def clear_cart(self):
        CartProduct.objects(cart=self).delete()
        self.save()

    @classmethod
    def get_orders(cls, telegram_id, isarchived=True):
        user = User.objects.get(telegram_id=telegram_id)
        cart = cls.objects.filter(user=user, is_archived=isarchived)
        return cart


class CartProduct(Document):
    cart = ReferenceField(Cart)
    product = ReferenceField('Product')


class Attributes(EmbeddedDocument):
    height = FloatField()
    weight = FloatField()
    width = FloatField()


class Category(Document):
    title = StringField(min_length=1, max_length=255, required=True, unique=False)
    subcategory = ListField(ReferenceField('self'))
    parent = ReferenceField('self')
    is_root = BooleanField(default=False)
    description = StringField(max_length=4096)

    def add_subcategory(self, cat_obj):
        cat_obj.parent = self
        cat_obj.save()

        self.subcategory.append(cat_obj)
        self.save()

    def is_parent(self):
        return bool(self.is_parent)

    @classmethod
    def create(cls, **kwargs):
        kwargs['subcategory'] = []
        if kwargs.get('parent') == True:
            kwargs['is_root'] = False

        return cls(**kwargs).save()

    def get_products(self):
        product = Product.objects.filter(category=self)
        return product


class Product(Document):
    article = StringField(max_length=32, required=True)
    title = StringField(min_length=1, max_length=255, required=True)
    description = StringField(max_length=4096)
    brand = StringField(max_length=255)
    price = IntField(min_value=1, required=True)
    in_stock = IntField(min_value=0, default=0)
    discount_price = IntField(min_value=1)
    discount_sign = IntField()
    attributes = EmbeddedDocumentField(Attributes)
    url_image = StringField(max_length=4096)
    extra_data = StringField(max_length=4096)
    category = ReferenceField(Category, required=True)

    def get_price(self):
        return self.discount_price if self.price > self.discount_price else self.price

    def get_quantity(self):
        return self.in_stock

    def get_product(self, product_id):
        return self.objects.get(id=product_id)

    @classmethod
    def get_promo_products(cls):
        promo = cls.objects.filter(discount_sign=1)
        return promo



class Texts(Document):
    TEXT_TYPE = (
        ('Greatings', 'Greatings'),
        ('News', 'News')
    )

    text_type = StringField(choices=TEXT_TYPE)
    body = StringField(max_length=2048)


if __name__ == "__main__":
    pass

    # ####Create structure catalog @#######
    # from structure_group import (category_dict, subcategori_dict)
    # import csv
    # # connect("shop_bot").drop_database("shop_bot")
    #
    # for root in category_dict:
    #     root_cat = Category.objects.create(**root)
    #     for sub in subcategori_dict:
    #         if root['title'] in sub.keys():
    #             if type(sub[root['title']])== list:
    #                 for itm in sub[root['title']]:
    #                     sub_cat = Category(**itm)
    #                     root_cat.add_subcategory(sub_cat)
    #             else:
    #                 sub_cat = Category(**sub[root['title']])
    #                 root_cat.add_subcategory(sub_cat)
    #
    # with open("items.csv", encoding='utf-8') as f:
    #     err = 0
    #     records = csv.DictReader(f, delimiter=';')
    #     # print(*records)
    #     for row in records:
    #         row["category"] = Category.objects.get(title=row["category"])
    #         Product.objects.create(**row)


            # Product.objects.create(
            #                         # category;
            #                         article=row["article"],
            #                         title=row["title"],
            #                         price=row["price"],
            #                         in_stock=row["in_stock"],
            #                         description=row["description"],
            #                         brand=row["brand"],
            #                         url_image=row["url_image"],
            #                         category=Category.objects.get(title=row["category"])
            #                         )




    # root_cat = Category.objects.create(**category_dict)
    #
    # for i in range(5):
    #     category_dict = {
    #         'title': f'Category sub {i}',
    #         'description': f'Category sub {i} description',
    #     }
    #     sub_cat = Category(**category_dict)
    #     root_cat.add_subcategory(sub_cat)
    # print(root_cat)

    # cats = Category.objects.filter(is_root=True)
    #
    # for cat in cats:
    #     print(cat)
    #
    #     if cat.subcategory:
    #         for sub in cat.subcategory:
    #             print({sub.parent})
    #             print({sub})

    ####ITEMS FREQUENCIES#####
    # user = User.objects.create(telegram_id='12345')
    # cart = Cart.objects.create(user=user)

    # cart = Cart.objects.first()
    # prodact = Product.objects.first()
    # cart.add_product_to_cart(prodact)
    # print(cart.get_cart())
    ####Подсчет кол-ва товаров ####
    # print(cart.get_cart().item_frequencies('product'))
    # freq = cart.get_cart().item_frequencies('product')
    # freq['product_id']

    # for i in range(10):
    #     prod = {'title': f'title{i}',
    #             'article': f'article{i}',
    #             'category': Category.objects.first(),
    #             'price': 10 * i + 1
    #             }
    #     create_product = Product.objects.create(**prod)
        # cart.add_product_to_cart(create_product)



    # 5e386297
    # aa5d9c72afb46610

