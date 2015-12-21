import multiprocessing
import Queue
import threading
import re
import traceback

import requests


class ParseWorker(multiprocessing.Process):
    def __init__(self, handlers, resp_queue, url_queue):
        super(ParseWorker, self).__init__()

        self.resp_queue = resp_queue
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
            url, response = self.resp_queue.get()
            try:
                handler, args = self.get_handler(url)

                result = handler.parse(response)
                handler.save(result, *args)
            except:
                print traceback.format_exc()


class RequestWorker(threading.Thread):
    def __init__(self, handlers, url_queue, resp_queue):
        super(RequestWorker, self).__init__()

        self.url_queue = url_queue
        self.resp_queue = resp_queue
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
                self.resp_queue.put((url, response))
            except:
                print traceback.format_exc()


class Application(object):
    def __init__(self, handlers, url_queue=None, resp_queue=None,
                 parse_worker_num=None, request_worker_num=3, **kwargs):
        super(Application, self).__init__()

        if not url_queue:
            url_queue = multiprocessing.Queue()
        if not resp_queue:
            resp_queue = multiprocessing.Queue(10)

        self.handlers = handlers
        self.url_queue = url_queue
        self._thread_url_queue = Queue.Queue()
        self.resp_queue = resp_queue

        if not parse_worker_num:
            parse_worker_num = multiprocessing.cpu_count()
        for i in range(parse_worker_num):
            ParseWorker(self.handlers, self.resp_queue, self.url_queue)

        for i in range(request_worker_num):
            RequestWorker(self.handlers, self._thread_url_queue, self.resp_queue)

    def run(self):
        while True:
            url = self.url_queue.get()

            self._thread_url_queue.put(url)


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