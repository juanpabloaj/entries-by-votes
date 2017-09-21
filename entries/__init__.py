# -*- coding: utf-8 -*-
import listparser
import feedparser
from urllib.parse import urlencode
import requests
import praw
import os
from math import pow
from time import mktime
from datetime import datetime
import binascii


def datetime_from_struct_time(struct_time):
    try:
        return datetime.fromtimestamp(mktime(struct_time))
    except OverflowError:
        print('Error with struct_time', struct_time)
        return datetime(1970, 1, 1)


def string_from_struct_time(struct_time):
    return datetime_from_struct_time(struct_time).strftime("%Y-%m-%d %H:%M:%S")


class Opml(object):

    def __init__(self):
        self.opml_url = (
            'https://raw.githubusercontent.com/kilimchoi/'
            'engineering-blogs/master/engineering_blogs.opml'
        )
        self.feeds = []

    def request_ompl(self):
        self.opml = listparser.parse(self.opml_url)

    def generate_feeds(self):
        feeds = []

        for feed in self.opml.feeds:
            feeds.append({'url': feed.url, 'title': feed.title})

        self.feeds = feeds

    def get_feeds(self):

        if self.feeds == []:
            self.request_ompl()
            self.generate_feeds()

        return self.feeds


class Entry(object):

    def __init__(self, raw_entry):
        self.raw_entry = raw_entry
        self.published = self.search_published_date(raw_entry)
        self.links = self.get_html_links(raw_entry.get('links', []))
        self.title = raw_entry.get('title', '')
        self.votes = []

    def age(self):
        return (datetime.now() - self.published)

    def hours_age(self):
        return self.age().total_seconds() / 3600.

    def days_age(self):
        return self.hours_age() / 24.

    def get_html_links(self, links):
        return [link.get('href', '') for link in links
                if link.get('type', None) == 'text/html']

    def search_published_date(self, entry):

        if entry.get('published_parsed', False):
            return datetime_from_struct_time(entry["published_parsed"])
        if entry.get('updated_parsed', False):
            return datetime_from_struct_time(entry["updated_parsed"])

        return datetime(1970, 1, 1)

    def set_votes(self, votes):
        self.votes = votes

    def get_total_votes(self):
        total = 0.0
        for vote in self.votes:
            total += vote['votes'] - 1

        return total

    def get_rank(self):
        try:
            return self.get_total_votes() / pow(self.hours_age() + 2., 1.8)
        except ValueError:
            return 0.0

    def __str__(self):
        return '<Entry: {}>'.format(self.title)


class Feed(object):

    def __init__(self, url, title):
        self.url = url
        self.title = title
        self.entries = []
        self.content = None

    def request_entries(self):
        try:
            self.content = feedparser.parse(self.url)
        except (UnicodeEncodeError, binascii.Error) as error:
            print('Error:', error, self.url)

    def parse_entries(self):

        if self.content is None:
            return

        raw_entries = self.content.entries
        entries = []

        if len(raw_entries) > 0:

            for entry in raw_entries:
                entries.append(Entry(entry))

        self.entries = entries

    def get_entries(self):

        if self.entries == []:
            self.request_entries()
            self.parse_entries()

        return self.entries

    def __str__(self):
        return '<Feed: {} {}>'.format(self.title, self.url)


class HackerNews(object):

    def __init__(self):
        self.api_url = 'https://hn.algolia.com/api/v1/search?'

    def search_url(self, url):
        query_url = urlencode({'query': url})
        request = self.api_url + query_url

        response = requests.get(request).json()

        return [hit for hit in response.get('hits', []) if hit['url'] == url]

    def votes_and_comments(self, url):
        hits = self.search_url(url)

        return [{
            'source': 'hacker_news',
            'votes': hit.get('points', 0),
            'comments': hit.get('num_comments', 0),
            'id': hit.get('objectID', 0)
        } for hit in hits]


class Reddit(object):

    def __init__(self):
        self.client = praw.Reddit(
            client_id=os.environ['PRAW_CLIENT_ID'],
            client_secret=os.environ['PRAW_CLIENT_SECRET'],
            user_agent=os.environ['PRAW_USER_AGENT']
        )

    def votes_and_comments(self, url):
        votes = []
        for sub in self.client.info(url=url):
            votes.append({
                'source': 'reddit',
                'subreddit': sub.subreddit.display_name,
                'votes': sub.ups, 'comments': sub.num_comments
            })

        return votes
