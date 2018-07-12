from tornado import web
from paho.mqtt.client import Client
import daiquiri
from exceptions import ConfigException
from websocket_handler import WebsocketHandler
from sse_handler import ServeSideEventsHandler
from threading import Thread
import time
logger = daiquiri.getLogger(__name__)


class Bridge(object):
    WEBSOCKETS = "websocket"
    SSE = "sse"

    def __init__(self, args, ioloop, dynamic_subscriptions):
        """ parse config values and setup Routes.
        """
        self.mqtt_topics = []
        try:
            self.mqtt_host = args["mqtt-to-server"]["broker"]["host"]
            self.mqtt_port = args["mqtt-to-server"]["broker"]["port"]
            self.bridge_port = args["server-to-client"]["port"]
            self.stream_protocol = args["server-to-client"]["protocol"]
            logger.info("Using protocol %s" % self.stream_protocol.lower())
            if self.stream_protocol.lower() != "websocket" and self.stream_protocol.lower() != "sse":
                raise ConfigException("Invalid protocol")
            self.dynamic_subscriptions = dynamic_subscriptions
            if not self.dynamic_subscriptions:
                self.mqtt_topics = args["mqtt-to-server"]["topics"]
        except KeyError as e:
            raise ConfigException("Error when accessing field", e) from e
        logger.info("connecting to mqtt")
        self.topic_dict = {}
        self.ioloop = ioloop
        self.mqtt_client = Client()
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.connect_async(
            host=self.mqtt_host, port=self.mqtt_port)
        self.mqtt_client.loop_start()
        self._app = web.Application([
            (r'.*', WebsocketHandler if self.stream_protocol ==
             "websocket" else ServeSideEventsHandler, dict(parent=self)),
        ])

    def get_app(self):
        return self._app
    def get_port(self):
        return self.bridge_port
    async def parse_req_path(self, req_path):
        candidate_path = req_path
        if len(candidate_path) is 1 and candidate_path[0] is "/":
            return "#"
        if candidate_path[len(req_path) - 1] is "/":
            candidate_path = candidate_path + "#"
        if candidate_path[0] == "/":
            candidate_path = candidate_path[1:]
        return candidate_path

    def on_mqtt_message(self, client, userdata, message):
        logger.debug("received message on topic %s" % message.topic)

    async def socket_write_message(self, socket, message):
        await socket.write_message(message)

    def append_dynamic(self, topic):
        logger.info("adding dynamic subscription for %s " % topic)
        self.message_callback_add_with_sub_topic(topic, dynamic=True)

    def remove_dynamic(self, topic):
        logger.info("removing dynamic subscription for %s " % topic)
        self.topic_dict.pop(topic, None)
        self.mqtt_client.unsubscribe(topic)

    def message_callback_add_with_sub_topic(self, sub_topic, dynamic):
        logger.info("adding callback for mqtt topic: %s" % sub_topic)

        def message_callback(client, userdata, message):
            logger.debug("Recieved Mqtt Message on %s as result of subscription on %s" % (
                message.topic, sub_topic))
            if sub_topic is not message.topic:
                if message.topic not in self.topic_dict[sub_topic]["matches"]:
                    self.topic_dict[sub_topic]["matches"].append(message.topic)
            for topic in self.topic_dict:
                if topic == message.topic:
                    for socket in self.topic_dict[topic]["sockets"]:
                        self.ioloop.add_callback(
                            self.socket_write_message, socket=socket, message=message.payload)
                elif message.topic in self.topic_dict[topic]["matches"]:
                    for socket in self.topic_dict[topic]["sockets"]:
                        self.ioloop.add_callback(
                            self.socket_write_message, socket=socket, message=message.payload)

        self.mqtt_client.message_callback_add(sub_topic, message_callback)
        self.topic_dict[sub_topic] = {
            "matches": [], "sockets": [], "dynamic": dynamic}

        self.mqtt_client.subscribe(sub_topic)

    def on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info("mqtt connected to broker %s:%s" %
                    (self.mqtt_host, str(self.mqtt_port)))
        for topic in self.mqtt_topics:
            self.message_callback_add_with_sub_topic(topic, dynamic=False)

    async def mqtt_disconnect(self):
        t = Thread(target=self.mqtt_client.disconnect, daemon=True)
        t.start()
        self.mqtt_client.loop_stop()
