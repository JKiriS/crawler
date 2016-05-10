# -*- coding: utf-8 -*-
import re
import traceback
import hashlib

import requests
import pymongo
import gevent
from bs4 import BeautifulSoup

from core import ge


class ForumHandler(ge.Handler):
    def initialize(self, db):
        self.db = db
        self.re_postid = re.compile("http://www\.lkong\.net/thread-(\d+)-.*")

    def request(self, url):
        return requests.get(url).text.encode('utf-8')

    def parse(self, html):
        soup = BeautifulSoup(html)

        next_page = soup.find('div', class_='pg').find('a', class_='nxt')
        if next_page and next_page.has_attr('href'):
            self.put_url(next_page['href'])

        posts = []
        table = soup.find('div', id='threadlist').find('form').find('table')
        if table:
            for tbody in table.find_all('tbody'):
                try:
                    url = tbody.find('a', class_='xst')['href']
                    title = tbody.find('a', class_='xst').get_text()
                    post = dict(url=url, title=title)
                    try:
                        by = tbody.find(class_='by')
                        post['user'] = by.find('a')['href']
                        post['post_time'] = by.find('em').get_text()
                    except:
                        pass
                    try:
                        stat = tbody.find(class_='num')
                        post['reply'] = int(stat.find('a').get_text())
                        post['view_num'] = int(stat.find('em').get_text())
                    except:
                        pass

                    mo = self.re_postid.match(post['url'])
                    if mo:
                        post['_id'] = mo.groups()[0]
                        posts.append(post)
                        self.put_url(url)
                except:
                    print traceback.format_exc()
        return posts

    def save(self, posts):
        if posts:
            try:
                self.db.post.insert_many(posts, ordered=False)
            except:
                print traceback.format_exc()


class PostHandler(ge.Handler):
    def initialize(self, db):
        self.db = db

    def request(self, url):
        return requests.get(url).text.encode('utf-8')

    def parse(self, html):
        soup = BeautifulSoup(html)

        books = []
        postlist = soup.find('div', id='postlist')
        if postlist:
            for book in postlist.find_all('a', href=re.compile("http://www\.yousuu\.com/name/")):
                try:
                    title = book.get_text()
                    if title.startswith(u'《'):
                        title = title[1:]
                    if title.endswith(u'》'):
                        title = title[:-1]

                    url = book['href']
                    books.append(dict(title=title, url=url, _id=hashlib.md5(url).hexdigest()))
                except:
                    print traceback.format_exc()

        return books

    def save(self, books, postid):
        if books:
            try:
                self.db.book.insert_many(books, ordered=False)
            except:
                print traceback.format_exc()
            self.db.post.update({'_id': postid}, {'books': map(lambda b: b['_id'], books)})

client = pymongo.MongoClient('115.156.196.9')
db = client['lkong']
db.authenticate('JKiriS', '910813gyb')


class Application(ge.Application):
    def __init__(self):
        settings = dict(
            worker_num=2,
        )

        handlers = [
            (r"http://www\.lkong\.net/forum\.php.*", ForumHandler, dict(db=db)),
            (r"http://www\.lkong\.net/thread-(\d+)-.*", PostHandler, dict(db=db)),
        ]
        queue = ge.MongoQueue('JKiriS', '910813gyb', host='115.156.196.9')

        super(Application, self).__init__(handlers, queue, **settings)


if __name__ == '__main__':
    app = Application()
    app.url_queue.put('http://www.lkong.net/forum.php?mod=forumdisplay&fid=60&filter=typeid&typeid=177')
    app.run()

