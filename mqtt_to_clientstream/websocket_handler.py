from tornado import websocket, gen
import daiquiri
logger = daiquiri.getLogger(__name__)


class WebsocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def initialize(self, parent):
        self.parent = parent

    @gen.coroutine
    def open(self):
        logger.debug('Websocket connection starting on uri: %s',
                     self.request.uri)
        req_topic = yield self.parent.parse_req_path(self.request.uri)
        logger.debug(
            "This socket will recive MQTT traffic on topic %s", req_topic)
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

    def on_close(self):
        topic_to_remove = None
        for topic in self.parent.topic_dict:
            if self in self.parent.topic_dict[topic]["sockets"]:
                self.parent.topic_dict[topic]["sockets"].remove(self)
                if len(self.parent.topic_dict[topic]["sockets"]) is 0 and self.parent.topic_dict[topic]["dynamic"]:
                    topic_to_remove = topic
        if topic_to_remove:
            self.parent.remove_dynamic(topic_to_remove)
