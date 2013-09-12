# encoding=utf-8

from lxml import html
from lxml import etree
from md5 import md5
from urlparse import urlparse
from urlparse import urljoin
from dateutil import parser
import time
from datetime import datetime

from cache import cache


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
    title = None

    def __init__(self, list_url, selectors, title=None):
        self.list_url = list_url
        assert 'links' in selectors
        assert 'title' in selectors
        assert 'body' in selectors
        assert 'date' in selectors
        assert 'author' in selectors
        self.selectors = selectors
        self.updated = date_to_atom(datetime.now())
        self.title = title

    def fetch(self):
        home = Page(self.list_url)
        for url, page in home.produce_pages_from_links(self.selectors['links'], check_cache=self.check_cache):
            if page is None:
                post = Post.from_dict(self.get_from_cache(url))
            else:
                post = Post.from_raw_page(page, self.selectors)
                self.save_to_cache(url, post.to_dict())
            yield post

    def check_cache(self, url):
        return cache.find({'url': url}).count()

    def get_from_cache(self, url):
        return cache.find_one({'url': url})

    def save_to_cache(self, url, post):
        cache.update({'url': url}, post, upsert=True)


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

    def produce_pages_from_links(self, selector, limit=None, check_cache=None):
        links = list(self.get_links(selector))
        if limit:
            links = links[:limit]
        total_links = len(links)
        for i, url in enumerate(links, 1):
            if check_cache and not check_cache(url):
                yield url, Page(url)
                if total_links > i and self.sleep:
                    time.sleep(self.sleep)
            else:
                yield url, None

    def get_text(self, selector):
        return self.html.cssselect(selector)[0].text

    def get_links(self, selector):
        return self.get_list(selector, lambda l: self.make_full_url(l.attrib.get('href')))

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

    cacheable_fields = 'url title body updated author_name atom_id inner_id'.split()

    @classmethod
    def from_raw_page(cls, page, selectors):
        post = Post()
        post.url = page.url
        post.title = page.get_text(selectors['title'])
        post.body = page.get_html(selectors['body'])
        post.updated = parser.parse(page.get_text(selectors['date']))
        post.author_name = page.get_text(selectors['author'])
        post.set_atom_id()
        return post

    @classmethod
    def from_dict(cls, data):
        post = Post()
        for f in cls.cacheable_fields:
            setattr(post, f, data[f])
        return post        

    def to_dict(self):
        return {f: getattr(self, f) for f in self.cacheable_fields}

    def make_atom_id(self):
        assert self.url
        assert self.updated
        slug = self.inner_id if self.inner_id else self.url
        return md5(slug).hexdigest()

    def set_atom_id(self):
        self.atom_id = self.make_atom_id()

    @property
    def updated_str(self):
        return date_to_atom(self.updated) if self.updated else ''

    @property
    def created_str(self):
        return date_to_atom(self.created) if self.created else ''

    def __unicode__(self):
        return u'Post: {}'.format(self.title)

    def __str__(self):
        return unicode(self).encode('utf-8')

