from mongoengine import *
from pprint import pprint
import pandas

connect('shop_bot', 'default', host='localhost')

class User(Document):
    STATES = (
        ('products', 'products'),
        ('categories', 'categories')
    )
    telegram_id = StringField(max_length=32, required=True, unique=True)
    username = StringField(max_length=128)
    fullname = StringField(max_length=256)
    phone_number = StringField(max_length=20)
    email = EmailField()
    state = StringField(choices=STATES)


class Cart(Document):
    user = ReferenceField(User)
    is_archived = BooleanField(default=False)

    @classmethod
    def get_or_create_cart(cls, user_id):
        user = User.objects.get(id=user_id)
        cart = cls.objects.get(user=user_id, is_archived=False)

        if not cart:
            cart = cls.objects.create(user=user)
        return cart


    def get_cart_products(self):
        return CartProduct.objects.filter(cart=self)

    def add_product_to_cart(self, product_id):
        CartProduct.objects.create(
            cart=self,
            product=Product.get_product(product_id)
        )

    def delete_product_from_cart(self, product):
        CartProduct.objects.filter(cart=self, product=product).first.delete()

    # To do overthink
    # def get_sum(self):
    #     return CartProduct.objects.


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
        Product.objects.filter(
            category=self
        )


class Product(Document):
    article = StringField(max_length=32, required=True)
    title = StringField(min_length=1, max_length=255, required=True)
    description = StringField(max_length=4096)
    price = IntField(min_value=1, required=True)
    in_stock = IntField(min_value=0, default=0)
    discount_price = IntField(min_value=1)
    attributes = EmbeddedDocumentField(Attributes)
    url_image = StringField(max_length=4096)
    extra_data = StringField(max_length=4096)
    category = ReferenceField(Category, required=True)

    def get_price(self):
        return self.price if not self.discount_price else self.discount_price

    def get_product(cls, **kwargs):
        cls.objects.get(**kwargs)

class Texts(Document):
    TEXT_TYPE = (
        ('Greatings', 'Greatings'),
        ('News', 'News')
    )

    text_type = StringField(choices=TEXT_TYPE)
    body = StringField(max_length=2048)



# if __name__ == "__main__":
    #####Create@#######
    # category_dict = {
    #     'title' : 'Category1',
    #     'description' : 'Category 1 description',
    #     'is_root' : True,
    # }
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

