#!/usr/bin/env python
# encoding=utf-8

import os
import sys
from flask import Flask, after_this_request
from jinja2 import Environment, PackageLoader
from parsers import Feed


app = Flask(__name__)

prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not prev_dir in sys.path:
    sys.path.append(prev_dir)

env = Environment(loader=PackageLoader('oryx', 'templates'))


@app.route('/<site_name>/feed.xml')
def feed(site_name):
    @after_this_request
    def add_header(response):
        response.headers['Content-type'] = 'application/atom+xml'
        return response

    feed = Feed('http://www.macworld.com/author/The-Macalope/', {
        'links': 'div.landing-listing > div.excerpt > a',
        'title': 'article h1',
        'body': 'article section.page',
        'date': 'article .article-meta [itemprop="datePublished"]',
        'author': 'article .author-info h3'
    })

    template = env.get_template('atom.xml')
    return template.render(
        site_title='The Macalope', site_url='http://oryx.vr2.net/', 
        feed_url='http://oryx.vr2.net/{}/feed.xml'.format(site_name),
        updated=feed.updated, articles=feed.fetch(),
        feed_id='http://oryx.vr2.net/{}/'.format(site_name)
    )


if __name__ == "__main__":
    app.run(debug=True)
