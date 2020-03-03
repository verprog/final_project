from flask import request
from flask_restful import Resource
from mongoengine import DoesNotExist

from api.schema import CategorySchema, ProductSchema
from models.model import Category, Product, User


class CategoryResource(Resource):
    """
    Category Resource to CRUD data for Categories
    """

    def get(self, cat_id=None):
        """GET method for categories
            :param cat_id ID of category. If absent - returns all the existing categories
        """
        many = not cat_id
        try:
            query = Category.objects.get(id=cat_id) if cat_id else Category.objects()
        except DoesNotExist:
            return {'msg': f'Category with id {cat_id} not exists'}
        return CategorySchema().dump(query, many=many)

    def post(self):
        """POST method for categories
        """
        err = CategorySchema().validate(request.json)

        if err:
            return err

        cat = Category(**request.json).save()
        return CategorySchema().dump(cat)

    def put(self, cat_id):
        """ PUT method for updating
        :param cat_id: category id that we want to update
        """
        if not cat_id:
            return {'msg': 'cat_id not defined for update'}
        cat = Category.objects.get(id=cat_id)
        cat.modify(**request.json)
        return CategorySchema().dump(cat)

    def delete(self, cat_id):
        """ DELETE method for remove category
       :param cat_id: category id that we want to delete
       """
        if not cat_id:
            return {'msg': 'cat_id not defined for update'}
        Category.objects.get(id=cat_id).delete()
        return {'msg': 'deleted'}


class ProductResource(Resource):
    def get(self, product_id=None):
        """GET method for select product
        :param product_id: product id that we want to select. If absent - seects all the products
        """
        many = not product_id
        try:
            query = Product.objects.get(id=product_id) if product_id else Product.objects()
        except DoesNotExist:
            return {'msg': f'Product with id {product_id} not exists'}
        return ProductSchema().dump(query, many=many)

    def post(self):
        """POST method for Product
        :return: The json with new project inserted
        """
        err = ProductSchema().validate(request.json)
        if err:
            return err
        product = Product(**request.json).save()
        return ProductSchema().dump(product)

    def put(self, product_id):
        """ PUT method for updating product
        :param product_id: product id that we want to update
        """
        if not product_id:
            return {'msg': 'cat_id not defined for update'}
        product = Product.objects.get(id=product_id)
        product.modify(**request.json)
        return ProductSchema().dump(product)

    def delete(self, product_id):
        """ DELETE method for remove product
        :param product_id: product id that we want to delete
        """
        if not product_id:
            return {'msg': 'cat_id not defined for update'}
        Product.objects.get(id=product_id).delete()
        return {'msg': 'deleted'}
