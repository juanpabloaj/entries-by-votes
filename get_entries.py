#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from entries import Opml, Feed
from entries import HackerNews, Reddit
from tornado import gen, queues
from tornado.ioloop import IOLoop
from concurrent.futures import ThreadPoolExecutor
from motor.motor_tornado import MotorClient

thread_pool = ThreadPoolExecutor(2)

feeds = queues.Queue()
entries = queues.Queue()
client = MotorClient(os.environ['MONGO_ENTRIES'])
db = client['entries-by-votes']


@gen.coroutine
def do_insert_entry(entry):
    yield db.entries.update_one(
        {'link': entry['link']}, {'$set': entry}, upsert=True
    )


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
        print('Fetching entry', current_entry.published, current_entry)
        try:
            for link in current_entry.links:
                votes = yield votes_from_entry(link)

                if votes != []:
                    current_entry.set_votes(votes)
                    print(
                        current_entry.published, current_entry.title,
                        link, current_entry.get_rank()
                    )
                    yield do_insert_entry({
                        'title': current_entry.title,
                        'link': link,
                        'published': current_entry.published,
                        'votes': current_entry.votes,
                        'total_votes': current_entry.get_total_votes(),
                        'rank': current_entry.get_rank()
                    })
            yield gen.sleep(1)
        finally:
            entries.task_done()


@gen.coroutine
def get_new_entries_from_feed():
    current_feed = yield feeds.get()
    print('Fetching feed', current_feed['url'])
    try:
        url, title = current_feed['url'], current_feed['title']
        for entry in (yield get_entries(url, title)):
            if entry.days_age() < 7:
                yield entries.put(entry)
    finally:
        feeds.task_done()


@gen.coroutine
def feeds_consumer():
    while True:
        yield get_new_entries_from_feed()


@gen.coroutine
def feeds_producer():
    for feed in (yield get_feeds()):
        yield feeds.put(feed)


@gen.coroutine
def entries_update():

    while True:
        print('Starting entries update')
        yield feeds_producer()
        yield feeds.join()
        yield entries.join()
        print('Entries updated done')
        yield gen.sleep(3600)


if __name__ == "__main__":
    IOLoop.current().spawn_callback(feeds_consumer)
    IOLoop.current().spawn_callback(entries_consumer)
    IOLoop.current().run_sync(entries_update)
