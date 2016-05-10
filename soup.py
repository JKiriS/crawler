# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup, SoupStrainer, Tag


if __name__ == '__main__':
    soup = BeautifulSoup(open('d:/crawler/pp.txt', 'r'))

    # for i in soup.find_all('div', class_='news_li').find('div',
    # class_='news_tu').find('img').get('src'):
    for i in soup.select('div.news_li div.news_tu').find('img').get('src'):
        print i
