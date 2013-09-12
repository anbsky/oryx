# encoding=utf-8

from lxml import html
from lxml import tostring
from md5 import md5
from urlparse import urlparse
from urlparse import urljoin
from dateutil import parser


class Feed(object):
    """
    Feed('http://www.macworld.com/author/The-Macalope/', {
        'links': 'div.landing-listing > div.excerpt > a',
        'title': 'article h1',
        'body': 'article section.page',
        'date': 'article .article-meta [itemprop="datePublished"]',
        'author': 'article .author-info h3'
        })
    """

    id = None
    root_url = None
    list_url = None

    def __init__(self, list_url, selectors):
        self.list_url = list_url
        assert 'links' in selectors
        assert 'title' in selectors
        assert 'body' in selectors
        assert 'date' in selectors
        assert 'author' in selectors
        self.selectors = selectors
        self.root_url = self.get_root_url(list_url)

    def get_root_url(self, url):
        location = urlparse(list_url)
        return '{}://{}'.format(location.scheme, location.netloc)

    def make_full_url(path):
        return urljoin(self.root_url, path)

    def fetch(self):
        links_page = Page(self.list_url)
        for link in links_page.get_links(self.selectors['links']):
            page = Page(self.make_full_url(link))
            post = Post()
            post.url = page.url
            post.title = post.get_text(self.selectors['title'])
            post.body = post.get_text(self.selectors['body'])
            post.updated = post.get_text(self.selectors['date'])
            post.author_name = post.get_text(self.selectors['author'])
            post.set_atom_id()
            yield post


class Page(object):
    url = None
    html = None
    sleep = None

    def __init__(self, url, sleep=2):
        self.url = url
        self.html = self.parse(url)
        self.sleep = sleep

    def parse(self, url):
        return html.parse(url).getroot()

    def get_text(selector):
        return self.html.cssselect(selector)[0].text

    def get_links(selector):
        return self.get_list(selector, lambda l: l.attrib.get('href'))

    def get_list(selector, getter=None):
        for item in self.html.cssselect(selector):
            yield getter(item) if getter else item

    def get_html(selector):
        return etree.tostring(self.html.cssselect(selector))


class Post(object):
    atom_id = None
    url = None
    title = None
    created = None
    updated = None
    body = None
    author_name = None
    author_email = None

    def make_atom_id(self):
        assert self.url
        assert self.date
        return md5(self.url + str(self.date))

    def set_atom_id(self):
        self.atom_id = self.make_atom_id()

    def __unicode__(self):
        return u'Post: {}'.format(self.title)
