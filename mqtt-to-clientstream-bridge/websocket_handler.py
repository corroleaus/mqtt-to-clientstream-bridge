from tornado import websocket
import daiquiri
logger = daiquiri.getLogger(__name__)


class WebsocketHandler(websocket.WebSocketHandler):
    def initialize(self, parent):
        self.parent = parent

    def check_origin(self, origin):
        return True

    def open(self):
        logger.debug('Websocket connection starting on uri: %s', self.request.uri)
        req_topic = self.parent.parse_req_path(self.request.uri)
        logger.debug("This socket will recive MQTT traffic on topic %s", req_topic)
        for topic in self.parent.topic_dict:
            if req_topic == topic:
                self.parent.topic_dict[topic]["sockets"].append(self)
            elif req_topic in self.parent.topic_dict[topic]["matches"]:
                self.parent.topic_dict[topic]["sockets"].append(self)

    def on_close(self):
        for topic in self.parent.topic_dict:
            if self in self.parent.topic_dict[topic]["sockets"]:
                self.parent.topic_dict[topic]["sockets"].remove(self)
