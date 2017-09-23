#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from tornado import ioloop, gen
from tornado import web
from motor.motor_tornado import MotorClient
from entries.get_entries import entries_update
from entries.get_entries import entries_consumer, feeds_consumer

client = MotorClient(os.environ['MONGO_ENTRIES'])
db = client['entries-by-votes']


class MainHandler(web.RequestHandler):

    @gen.coroutine
    def get(self):
        db = self.settings['db']

        cursor = db.entries.find({"rank": {"$gt": 0}})\
            .sort('rank', -1).limit(100)
        entries = yield cursor.to_list(length=100)

        self.render('templates/index.html', entries=entries)


def make_app():
    return web.Application([
        (r'/', MainHandler),
    ], db=db)


if __name__ == "__main__":
    port = os.environ.get('TORNADO_PORT', 8888)
    print('Starting app in port {}'.format(port))
    app = make_app()
    app.listen(port)
    io_loop = ioloop.IOLoop.current()
    io_loop.spawn_callback(feeds_consumer)
    io_loop.spawn_callback(entries_consumer)
    io_loop.spawn_callback(entries_update)
    io_loop.start()
