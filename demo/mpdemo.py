# -*- coding: utf-8 -*-
import requests
import time
from pymongo import MongoClient

from core import mp


class TestHandler(mp.Handler):
    def initialize(self):
        self.s = requests.Session()
        client = MongoClient('115.156.196.9')
        mongo = client['md']
        mongo.authenticate('JKiriS', '910813gyb')
        self.mongo = mongo

    def request(self, url):
        return self.s.get(url).text.encode('utf-8')

    def parse(self, html):
        self.put_url('http://www.acfun.tv')
        return [dict(name='11', age=1)]

    def save(self, items, a, b):
        self.mongo.test.insert_many(items)


class Application(mp.Application):
    def __init__(self):
        settings = dict(
            parse_worker_num=1,
        )

        handlers = [
            (r"http://([^\.]+)\.([^\d]+)\..*", TestHandler),
        ]

        super(Application, self).__init__(handlers, **settings)


if __name__ == '__main__':
    app = Application()
    app.url_queue.put('http://www.baidu.com')
    app.run()