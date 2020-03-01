from models.model import *
from models.structure_group import (category_dict, subcategori_dict)
import csv
from mongoengine import *

if __name__ == "__main__":

    try:
        disconnect_all()
        connect('shop_bot').drop_database("shop_bot")
        print('drop base')
    except Exception as ex:
        print(ex)

    ####Create structure catalog @#######
    for root in category_dict:
        root_cat = Category.objects.create(**root)
        for sub in subcategori_dict:
            if root['title'] in sub.keys():
                if type(sub[root['title']] )== list:
                    for itm in sub[root['title']]:
                        sub_cat = Category(**itm)
                        root_cat.add_subcategory(sub_cat)
                else:
                    sub_cat = Category(**sub[root['title']])
                    root_cat.add_subcategory(sub_cat)

    ####Filling catalog wares #######
    with open("items.csv", encoding='utf-8') as f:
        err = 0
        records = csv.DictReader(f, delimiter=';')
        for row in records:
            row["category"] = Category.objects.get(title=row["category"])
            Product.objects.create(**row)