from tornado import ioloop
import yaml
import logging
import daiquiri
import signal
import time
import sys
from pathlib import Path
import argparse
from bridge import Bridge
from exceptions import ConfigException
daiquiri.setup(level=logging.INFO)

logger = daiquiri.getLogger(__name__)


class App(object):
    """ main application
    """

    def __init__(self, config_path, dynamic_subscriptions):
        self.config = self.parse_config(Path(config_path).resolve())
        self.dynamic_subscriptions = dynamic_subscriptions
        self.ioloop = ioloop.IOLoop.instance()
        self.bridge = Bridge(self.config, self.ioloop, self.dynamic_subscriptions)
        signal.signal(signal.SIGINT, self.sig_handler)

    def start(self):
        """ Start the bridge
        """
        self.bridge.get_app().listen(8080)
        self.ioloop.start()

    def parse_config(self, config_path):
        """ Parse application config file
        """
        logger.info("Using Config: %s" % config_path)
        try:
            with open(config_path, 'r') as stream:
                try:
                    return yaml.load(stream)
                except yaml.YAMLError as e:
                    raise ConfigException("Error when parsing config", e)
        except FileNotFoundError as e:
            raise ConfigException("Configfile not found", e) from e

    def shutdown(self):
        """ Cleanup MQTT client and ioloop.
        """
        logger.info('Stopping server.')
        self.bridge.mqtt_client.disconnect()
        self.bridge.mqtt_client.loop_stop()
        ioloop.IOLoop.instance().stop()
        sys.exit(0)

    def sig_handler(self, sig, frame):
        """ Basic Signal Handler
        """
        logger.info('Caught signal: %s', sig)
        ioloop.IOLoop.instance().add_callback(self.shutdown)


def main():
    """ Parse args and initialize app
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True,
                        help='Configuration file')
    parser.add_argument('-d', '--dynamic-subscriptions', action='store_true',
                        help='If Dynamic subscriptions is set, the application will subscribe to topics dynamically based on http requests.')
    parser.add_argument('-l', '--log-level', required=False, choices=[
                        'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='Log Level')
    args = parser.parse_args()
    if args.log_level:
        daiquiri.setup(level=getattr(logging, args.log_level))
    logger.info("initializing...")
    app = App(args.config, args.dynamic_subscriptions)
    app.start()


if __name__ == "__main__":
    main()
