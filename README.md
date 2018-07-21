# mqtt-to-clientstream-bridge

MQTT to ClientStream(websocket/sse) Bridge


## Why

Skip the backend part of connection you webapp to MQTT, instead configure this app with a broker and it will serve a websocket or SSE server, bridging any incomming mqtt packets to your webapp.


## How

**Usage**

```
usage: mqtt-bridge [-h] [-c CONFIG] [-b BROKER_HOST] [-i BROKER_PORT]
                   [-p BRIDGE_PORT] [-s {websocket,sse}] [-d]
                   [-l {CRITICAL,ERROR,WARNING,INFO,DEBUG}]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -b BROKER_HOST, --broker-host BROKER_HOST
                        Broker Host
  -i BROKER_PORT, --broker-port BROKER_PORT
                        Mqtt broker port
  -p BRIDGE_PORT, --bridge-port BRIDGE_PORT
                        Listening port of the Bridge server
  -s {websocket,sse}, --protocol {websocket,sse}
                        Protocol -- websocket or sse
  -d, --dynamic-subscriptions
                        If Dynamic subscriptions is set, the application will
                        subscribe to topics dynamically based on http
                        requests. If a config file is used, the topics list
                        may be omitted.
  -l {CRITICAL,ERROR,WARNING,INFO,DEBUG}, --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Log Level
```

**Build as Docker Container**

```make image```

```docker run -it mqtt-bridge --help```


**Develop**

```make init```

```source env/bin/activate```

```pip3 install -e .```

```python3.6 mqtt_to_clientstream/app.py -c config/config.example.yaml```

