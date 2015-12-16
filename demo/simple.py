# -*- coding: utf-8 -*-
import requests

import core


class TestHandler(core.Handler):
    def initialize(self, s):
        self.s = s

    def request(self, url):
        return self.s.get(url).text.encode('utf-8')

    def parse(self, html):
        return [dict(name='11', age=1)]

    def save(self, items, a, b):
        for item in items:
            print item

s = requests.Session()


class Application(core.Application):
    def __init__(self):
        settings = dict(
            worker_num=2,
        )

        handlers = [
            (r"http://([^\.]+)\.([^\d]+)\..*", TestHandler, dict(s=s)),
        ]

        hub = core.Hub()
        hub.put('http://www.baidu.com')

        super(Application, self).__init__(handlers, hub, **settings)


if __name__ == '__main__':
    app = Application()
    app.run()