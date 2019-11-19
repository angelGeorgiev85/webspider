# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import json


class WebspiderPipeline(object):

    def process_item(self, input_item, spider):
        item = {
            "name": input_item["productname"],
            "price": self.clear_price(input_item["productcart"]),
            "img": self.clear_img(input_item["img"]),
            "characteristics": {self.clear_data(k): self.clear_data(v)
                                for k, v in input_item["characteristics"].items()
                                },
            "store_availability": input_item["availability"]
        }
        return item

    def clear_price(self, price):
         return price.split()[0].replace(",",".")

    def clear_data(self, string):
        string = re.sub(r'[\s]+', '', string)
        return re.search('>([^<>]*)<', string).group(1)

    def clear_img(self, img_str):
        img_str = re.search('src="([^"]+)"', img_str).group(1)
        return img_str
		

    
