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
    def __init__(self, config_path):
        self.config = self.parse_config(Path(config_path).resolve())
        self.ioloop = ioloop.IOLoop.instance()
        self.bridge = Bridge(self.config, self.ioloop)
        signal.signal(signal.SIGINT, self.sig_handler)

    def start(self):
        self.bridge.get_app().listen(8080)
        self.ioloop.start()

    def parse_config(self, config_path):
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
        logger.info('Stopping server.')
        self.bridge.mqtt_client.disconnect()
        self.bridge.mqtt_client.loop_stop()
        ioloop.IOLoop.instance().stop()
        sys.exit(0)

    def sig_handler(self, sig, frame):
        logger.info('Caught signal: %s', sig)
        ioloop.IOLoop.instance().add_callback(self.shutdown)


def main():
    logger.info("initializing bridge")
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Configuration file')
    parser.add_argument('--log-level', required=False, choices=[
                        'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='Log Level')
    args = parser.parse_args()
    if args.log_level:
        daiquiri.setup(level=getattr(logging, args.log_level))
    app = App(args.config)
    app.start()


if __name__ == "__main__":
    main()
