# -*- coding: utf-8 -*-
import re
import requests
import traceback

from gevent import monkey; monkey.patch_all()
import gevent
from gevent import queue
from gevent import Greenlet


class Handler(object):
    def __init__(self, app, url):
        self.app = app
        self.url = url

    def initialize(self):
        pass

    def put(self, url):
        self.app.hub.put(url)

    def request(self, url):
        return requests.get(url).text.encode('utf-8')

    def parse(self, html):
        return []

    def save(self, items):
        pass


class Hub(object):
    def __init__(self):
        self.queue = queue.JoinableQueue()

    def get(self):
        return self.queue.get()

    def put(self, item):
        self.queue.put(item)

    def task_done(self, url):
        self.queue.task_done()

    def run(self):
        self.queue.join()


class Worker(Greenlet):
    def __init__(self, app):
        super(Worker, self).__init__()

        self.app = app

        self.start()

    def run(self):
        while True:
            url = self.app.hub.get()
            try:
                handler, args = self.app.get_handler(url)

                response = handler.request(url)
                result = handler.parse(response)
                handler.save(result, *args)
            except:
                print traceback.format_exc()
            finally:
                self.app.hub.task_done(url)
                gevent.sleep(.1)


class Application(object):
    def __init__(self, handlers, hub, worker_num=3, **kwargs):
        self.handlers = handlers
        self.hub = hub

        for _ in range(worker_num):
            Worker(self)

    def get_handler(self, url):
        for handler in self.handlers:
            mo = re.match(handler[0], url)
            if mo:
                h = handler[1](self, url)
                if len(handler) == 3:
                    h.initialize(**handler[2])
                return h, mo.groups()
        else:
            raise Exception('no handler matched')

    def run(self):
        self.hub.run()