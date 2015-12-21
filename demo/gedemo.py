# -*- coding: utf-8 -*-
import requests
import gevent

from core import ge


class TestHandler(ge.Handler):
    def initialize(self, s):
        self.s = s

    def request(self, url):
        return self.s.get(url).text.encode('utf-8')

    def parse(self, html):
        print html
        self.put_url('http://www.acfun.tv')
        gevent.sleep(10)
        return [dict(name='11', age=1)]

    def save(self, items, a, b):
        for item in items:
            print item

s = requests.Session()


class Application(ge.Application):
    def __init__(self):
        settings = dict(
            worker_num=2,
        )

        handlers = [
            (r"http://([^\.]+)\.([^\d]+)\..*", TestHandler, dict(s=s)),
        ]

        super(Application, self).__init__(handlers, **settings)


if __name__ == '__main__':
    app = Application()
    app.url_queue.put('http://www.baidu.com')
    app.run()