# -*- coding: utf-8 -*-
from scrapy.http import FormRequest
import scrapy
import re
import json

class SpiderSpider(scrapy.Spider):
    name = 'spider'
   
    domain = 'https://mr-bricolage.bg'
    home_url = 'https://mr-bricolage.bg/bg/Instrumenti/Avto-i-veloaksesoari/Veloaksesoari/c/006008012'
	
    custom_settings = {
        'FEED_URI' : 'tmp/report.json'
    }
	
    latitude = None
    longitude = None
    tmp = []
    item_id = 0
    passed_first_results_page = False
	
    def start_requests(self):
        self.start_urls = [
            self.home_url,
            self.domain + '/wro/all_responsive.js'
        ]
        for priority, url in enumerate(self.start_urls):
            yield scrapy.Request(url=url, 
			                    priority=priority, 
								callback=self.parse_latitude_longitude)

			
    def parse_latitude_longitude(self, response):
        try:
            self.latitude = re.search('latitude:(\-?[0-9]{1,2}\.?[0-9]*)',response.text).group(1)
            self.longitude = re.search('longitude:(\-?[0-9]{1,3}\.?[0-9]*)',response.text).group(1)
        except AttributeError:
            msg = "Can't extract latitude/longitude coordinates."
            self.alert(msg, False)
        for _ in self.parse_items_pages(response):
            yield _
			
    def parse_items_pages(self, response):
        links = response.css('a[href*="/p/"][title]::attr(href)').extract()
        for link in links:
            yield scrapy.Request(
			    response.urljoin(link), 
				callback=self.parse_item)
        if not self.passed_first_results_page:
            self.passed_first_results_page = True
            page_num_url_init_string = response.url.replace(self.start_urls[0], "")
            page_num_url_init_string += "?q=%3Arelevance&page="
            pages = response.css('a[class=""][href*="%s"]::attr(href)' %
                                 page_num_url_init_string).extract()
            for page in pages:
                yield scrapy.Request(
				    response.urljoin(page), 
					callback=self.parse_items_pages)		
    
			
    def parse_item(self, response):
        selector_key = '.product-classifications table tr :nth-child(1)'
        selector_val = '.product-classifications table tr :nth-child(2)'
        characteristics_key = response.css(selector_key).extract()
        characteristics_val = response.css(selector_val).extract()
        res = {'characteristics': dict(zip(characteristics_key, characteristics_val))}

        stock_fields = [
		    "actionurl",
            "cartpage",
            "entryNumber",
            "productname",
            "productcart",
            "img"
        ]
       
        for field in stock_fields:
            res.update({
                field: str(response.css('a[href="#stock"]::attr(data-%s)' %
				        field).extract_first())
            })
			
        self.tmp.append(res)
		
        data = {
            "cartPage": res["cartpage"],
            "entryNumber": res["entryNumber"] if res["entryNumber"] != "None" else "0",
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        if self.latitude is not None:
            yield FormRequest(self.url(res["actionurl"]), method='POST', 
                formdata=data, callback=self.store_availability)
      
    	
    def store_availability(self, response):
        stores = json.loads(response.text)["data"]
        availability = [
		    {
			    "Name": store["displayName"],
				"Town": store["town"],
				"Address": store["line1"],
				"Stock": store["stockPickup"].replace("&nbsp;"," ")
            } for store in stores
        ]
        self.tmp[self.item_id].update({"availability": availability})
        yield self.tmp[self.item_id]
        self.item_id += 1 
        
		
    def url(self, link):
        return self.domain + link	
		

    def alert(self, msg, is_fatal=True):
        if not is_fatal:
            print(msg)
        
    