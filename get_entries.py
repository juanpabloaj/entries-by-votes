#!/usr/bin/python
# -*- coding: utf-8 -*-
from entries import Opml, Feed
from entries import HackerNews, Reddit
from tornado import gen, queues
from tornado.ioloop import IOLoop
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(2)

feeds = queues.Queue()
entries = queues.Queue()


@gen.coroutine
def get_feeds():
    return (yield thread_pool.submit(Opml().get_feeds))


@gen.coroutine
def get_entries(url, title):
    return (yield thread_pool.submit(Feed(url, title).get_entries))


@gen.coroutine
def votes_from_hacker_news(url):
    return (yield thread_pool.submit(HackerNews().votes_and_comments, url))


@gen.coroutine
def votes_from_reddit(url):
    return (yield thread_pool.submit(Reddit().votes_and_comments, url))


@gen.coroutine
def votes_from_entry(link):
    votes = []

    for vote in (yield votes_from_hacker_news(link)):
        votes.append(vote)
    for vote in (yield votes_from_reddit(link)):
        votes.append(vote)

    return votes


@gen.coroutine
def entries_consumer():
    while True:
        current_entry = yield entries.get()

        for link in current_entry.links:
            votes = yield votes_from_entry(link)

            if votes != []:
                current_entry.set_votes(votes)
                print(
                    current_entry, current_entry.days_age(),
                    current_entry.links, current_entry.get_rank()
                )
        yield gen.sleep(1)


@gen.coroutine
def get_new_entries_from_feed():
    current_feed = yield feeds.get()
    url, title = current_feed['url'], current_feed['title']
    for entry in (yield get_entries(url, title)):
        if entry.days_age() < 7.:
            yield entries.put(entry)


@gen.coroutine
def feeds_consumer():
    while True:
        yield get_new_entries_from_feed()


@gen.coroutine
def feeds_producer():
    for feed in (yield get_feeds()):
        yield feeds.put(feed)


@gen.coroutine
def main():

    IOLoop.current().spawn_callback(feeds_consumer)
    IOLoop.current().spawn_callback(entries_consumer)

    yield feeds_producer()
    yield feeds.join()


if __name__ == "__main__":
    print('Starting ...')
    IOLoop.current().run_sync(main)
