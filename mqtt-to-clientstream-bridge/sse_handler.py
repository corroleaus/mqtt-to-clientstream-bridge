from tornado import web
import daiquiri
logger = daiquiri.getLogger(__name__)


class ServeSideEventsHandler(web.RequestHandler):
    def initialize(self, parent):
        self.parent = parent
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')
        self.connected_clients = []

    def get(self):
        logger.debug('sse request received on uri: %s',
                     self.request.uri)
        req_topic = self.parent.parse_req_path(self.request.uri)
        logger.debug(
            "This connection will recive MQTT traffic on topic %s", req_topic)
        for topic in self.parent.topic_dict:
            if req_topic == topic:
                self.parent.topic_dict[topic]["sockets"].append(self)
                return
            elif req_topic in self.parent.topic_dict[topic]["matches"]:
                self.parent.topic_dict[topic]["sockets"].append(self)
                return
        if self.parent.dynamic_subscriptions:
            self.parent.append_dynamic(req_topic)
            self.parent.topic_dict[req_topic]["sockets"].append(self)

    def close(self):
        self.on_close()

    def write_message(self, data):
        self.write(data)
        self.flush()
        self.finnish()

    def on_close(self):
        topic_to_remove = None
        for topic in self.parent.topic_dict:
            if self in self.parent.topic_dict[topic]["sockets"]:
                self.parent.topic_dict[topic]["sockets"].remove(self)
                if len(self.parent.topic_dict[topic]["sockets"]) is 0 and self.parent.topic_dict[topic]["dynamic"]:
                    topic_to_remove = topic
        if topic_to_remove:
            self.parent.remove_dynamic(topic_to_remove)
