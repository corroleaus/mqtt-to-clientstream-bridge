import daiquiri

from tornado import gen, web
from tornado.iostream import StreamClosedError
import time
logger = daiquiri.getLogger(__name__)


class ServeSideEventsHandler(web.RequestHandler):

    def initialize(self, parent):
        logger.debug(self)
        self.parent = parent
        self._data = None
        self._should_publish = False
        self._last_data = None

    @gen.coroutine
    def close(self):
        yield self.on_close()

    @gen.coroutine
    def publish(self, data):
        self.write('event: {}\n'.format("mqtt"))
        self.write('data: {}\n\n'.format(data))
        yield self.flush()

    @gen.coroutine
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')
        logger.debug('sse request received on uri: %s',
                     self.request.uri)
        req_topic = yield self.parent.parse_req_path(self.request.uri)
        logger.debug(
            "This connection will recive MQTT traffic on topic %s", req_topic)
        match_found = False
        for topic in self.parent.topic_dict:
            if req_topic == topic:
                self.parent.topic_dict[topic]["sockets"].append(self)
                match_found = True
                break
            elif req_topic in self.parent.topic_dict[topic]["matches"]:
                self.parent.topic_dict[topic]["sockets"].append(self)
                match_found = True
                break
        if self.parent.dynamic_subscriptions and not match_found:
            self.parent.append_dynamic(req_topic)
            if self not in self.parent.topic_dict[req_topic]["sockets"]:
                self.parent.topic_dict[req_topic]["sockets"].append(self)
        logger.debug(self.parent.topic_dict)
        logger.debug("connection setup")
        sleep_time = .01  # Second
        ping_freq = .5  # Hz
        ping = 'event: ping\ndata: \n\n'
        c = 0
        while True:
            try:
                c += 1
                if self._should_publish:
                    yield self.publish(self._data)
                    self._should_publish = False
                else:
                    if c == int((1/sleep_time)/ping_freq):
                        logger.debug("pinging")
                        yield self.write(ping)
                        yield self.flush()
                        c = 0
                    yield gen.sleep(sleep_time)
            except StreamClosedError:
                yield self.close()
                break
        logger.debug("connection end")
        yield self.finish()

    async def write_message(self, data):
        self._data = data
        self._should_publish = True

    @gen.coroutine
    def on_close(self):
        logger.debug("closing connection")
        topic_to_remove = None
        for topic in self.parent.topic_dict:
            if self in self.parent.topic_dict[topic]["sockets"]:
                self.parent.topic_dict[topic]["sockets"].remove(self)
                if len(self.parent.topic_dict[topic]["sockets"]) is 0 and self.parent.topic_dict[topic]["dynamic"]:
                    topic_to_remove = topic
        if topic_to_remove:
            self.parent.remove_dynamic(topic_to_remove)
