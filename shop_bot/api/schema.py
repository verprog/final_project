from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.String()
    telegram_id = fields.Int(min_value=0)
    username = fields.String(max_length=128)
    fullname = fields.String(max_length=256)
    phone_number = fields.String(max_length=20)
    email = fields.String()
    create_user = fields.DateTime()


class CategorySchema(Schema):
    id = fields.String()
    title = fields.String(min_length=1, max_length=255, required=True, unique=False)
    subcategory = fields.List(fields.String, dump_only=True)
    parent = fields.String()
    is_root = fields.Bool(default=False)
    description = fields.String(max_length=4096)


class ProductSchema(Schema):
    id = fields.String()
    article = fields.String(max_length=32, required=True)
    title = fields.String(min_length=1, max_length=255, required=True)
    description = fields.String(max_length=4096)
    brand = fields.String(max_length=255)
    price = fields.Int(min_value=1, required=True)
    in_stock = fields.Int(min_value=0, default=0)
    discount_price = fields.Int(min_value=1)
    discount_sign = fields.Int()
    attributes = fields.String()
    url_image = fields.String(max_length=4096)
    extra_data = fields.String(max_length=4096)
    category = fields.String()
