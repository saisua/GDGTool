import scrapy
from functools import partial
import re

url_re = re.compile(r"(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})?\/([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")

max_depth = 1
class MySpider(scrapy.Spider):
	name = 'scrapy_test'
	start_urls = ['https://crawler-test.com/']
	#start_urls = ['https://duckduckgo.com/?t=ffab&q=scraping+test&atb=v320-1&ia=web']
	
	def parse(self, response, depth=0):
		if(depth == max_depth):
			return
		for href in response.css('a::attr(href)'):
			print(href.extract(), depth)
			if(url_re.match(href.extract())):
				yield response.follow(href, partial(self.parse, depth=depth+1))
