#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from tornado import ioloop, gen
from tornado import web
from motor.motor_tornado import MotorClient

client = MotorClient(os.environ['MONGO_ENTRIES'])
db = client['entries-by-votes']


class MainHandler(web.RequestHandler):

    @gen.coroutine
    def get(self):
        db = self.settings['db']

        cursor = db.entries.find({}).sort('rank', -1)
        entries = yield cursor.to_list(length=100)

        self.render('index.html', entries=entries)


def make_app():
    return web.Application([
        (r'/', MainHandler),
    ], db=db)


if __name__ == "__main__":
    port = os.environ.get('TORNADO_PORT', 8888)
    print('Starting app in port {}'.format(port))
    app = make_app()
    app.listen(port)
    ioloop.IOLoop.current().start()
