# encoding=utf-8

from lxml import html
from lxml import etree
from md5 import md5
from urlparse import urlparse
from urlparse import urljoin
from dateutil import parser
import time
from datetime import datetime


def date_to_atom(date):
    return date.replace(microsecond=0).isoformat('T')


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
    updated = None

    def __init__(self, list_url, selectors):
        self.list_url = list_url
        assert 'links' in selectors
        assert 'title' in selectors
        assert 'body' in selectors
        assert 'date' in selectors
        assert 'author' in selectors
        self.selectors = selectors
        self.updated = date_to_atom(datetime.now())

    def fetch(self):
        links_page = Page(self.list_url)
        for page in links_page.produce_pages_from_links(self.selectors['links'], limit=2):
            post = Post()
            post.url = page.url
            post.title = page.get_text(self.selectors['title'])
            post.body = page.get_html(self.selectors['body'])
            post.updated = parser.parse(page.get_text(self.selectors['date']))
            post.author_name = page.get_text(self.selectors['author'])
            post.set_atom_id()
            yield post


class Page(object):
    url = None
    html = None
    sleep = None

    def __init__(self, url, sleep=2):
        self.url = url
        self.root_url = self.get_root_url(url)
        self.html = self.parse(url)
        self.sleep = sleep

    @classmethod
    def get_root_url(cls, url):
        location = urlparse(url)
        return '{}://{}'.format(location.scheme, location.netloc)

    def make_full_url(self, path):
        return urljoin(self.root_url, path) if not urlparse(path).netloc else path

    def parse(self, url):
        return html.parse(url).getroot()

    def produce_pages_from_links(self, selector, limit=None):
        links = list(self.get_links(selector))
        if limit:
            links = links[:limit]
        total_links = len(links)
        for i, url in enumerate(links, 1):
            yield Page(self.make_full_url(url))
            if total_links > i and self.sleep:
                time.sleep(self.sleep)

    def get_text(self, selector):
        return self.html.cssselect(selector)[0].text

    def get_links(self, selector):
        return self.get_list(selector, lambda l: l.attrib.get('href'))

    def get_list(self, selector, getter=None):
        for item in self.html.cssselect(selector):
            yield getter(item) if getter else item

    def get_html(self, selector):
        return etree.tostring(self.html.cssselect(selector)[0])


class Post(object):
    atom_id = None
    url = None
    title = None
    created = None
    updated = None
    body = None
    author_name = None
    author_email = None
    inner_id = None

    def make_atom_id(self):
        assert self.url
        assert self.updated
        slug = self.inner_id if self.inner_id else self.url
        return md5(slug).hexdigest()

    def set_atom_id(self):
        self.atom_id = self.make_atom_id()

    @property
    def updated_str(self):
        return date_to_atom(self.updated)

    def __unicode__(self):
        return u'Post: {}'.format(self.title)

    def __str__(self):
        return unicode(self).encode('utf-8')