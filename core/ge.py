# -*- coding: utf-8 -*-
"""
simple one process multiple coroutine crawler based on gevent.
"""
import re
import requests
import traceback
import time

from gevent import monkey; monkey.patch_all()
import gevent
from gevent import Greenlet
from gevent.queue import Queue
import pymongo
from bson.objectid import ObjectId


class MongoQueue(Queue):
    def __init__(self, username, password, database='queue', collection='url', host='127.0.0.1', port=27017):
        super(MongoQueue, self).__init__()

        client = pymongo.MongoClient(host, port)
        db = client[database]
        db.authenticate(username, password)
        self.collection = db.get_collection(collection)

        self.last = None
        urls = self.collection.find_one({'status': 1})
        if urls:
            self.last = urls['_id']
            for url in urls.get('urls', []):
                super(MongoQueue, self).put(url)

    def get(self, *args, **kwargs):
        if super(MongoQueue, self).empty():
            try:
                self.collection.update({'_id': ObjectId(self.last), 'status': 1}, {'$set': {'status': 2}})
            except:
                pass
            urls = self.collection.find_one_and_update({'status': 0}, {'$set': {'status': 1}})
            if urls:
                self.last = urls['_id']
                for url in urls.get('urls', []):
                    super(MongoQueue, self).put(url)

        return super(MongoQueue, self).get(*args, **kwargs)

    def put(self, item, *args, **kwargs):
        if super(MongoQueue, self).qsize() >= 50:
            urls = []
            while not super(MongoQueue, self).empty():
                urls.append(super(MongoQueue, self).get())
            self.collection.insert_one({'status': 0, 'urls': urls})

        super(MongoQueue, self).put(item, *args, **kwargs)


class Handler(object):
    def __init__(self, url, url_queue):
        self.url_queue = url_queue
        self.url = url

    def initialize(self):
        pass

    def put_url(self, url):
        self.url_queue.put(url)

    def request(self, url):
        return requests.get(url).text.encode('utf-8')

    def parse(self, html):
        return []

    def save(self, items):
        pass


class Worker(Greenlet):
    def __init__(self, handlers, url_queue):
        super(Worker, self).__init__()

        self.url_queue = url_queue
        self.handlers = handlers
        self._handlers = None

        self.start()

    def prepare(self, handler):
        h = handler[1](None, self.url_queue)
        if len(handler) == 3:
            h.initialize(**handler[2])
        else:
            h.initialize()
        return handler[0], h

    def get_handler(self, url):
        if not self._handlers:
            self._handlers = map(self.prepare, self.handlers)

        for handler in self._handlers:
            mo = re.match(handler[0], url)
            if mo:
                handler[1].url = url
                return handler[1], mo.groups()
        else:
            raise Exception('no handler matched')

    def run(self):
        while True:
            url = self.url_queue.get()
            try:
                handler, args = self.get_handler(url)

                response = handler.request(url)
                result = handler.parse(response)
                handler.save(result, *args)
            except:
                print traceback.format_exc()


class Application(object):
    def __init__(self, handlers, url_queue=None, worker_num=3, **kwargs):
        self.handlers = handlers

        if not url_queue:
            url_queue = Queue()
        self.url_queue = url_queue

        for _ in range(worker_num):
            Worker(self.handlers, self.url_queue)

    def run(self):
        while True:
            time.sleep(100000)