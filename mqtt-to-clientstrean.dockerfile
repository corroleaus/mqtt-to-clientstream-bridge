FROM python:3.6-alpine
LABEL maintainer="pontus.pohl@gmail.com"

WORKDIR /srv

COPY . .

RUN apk update && \
apk --no-cache add ca-certificates \
py-yaml py3-paho-mqtt py3-tornado \
&& rm -rf /var/cache/apk/

ENV PYTHONPATH="${PYTHONPATH}:/usr/lib/python3.6/site-packages/"

RUN python setup.py install --prefix=/usr && rm -rf /srv/*

ENTRYPOINT ["/usr/bin/mqtt-bridge"]
CMD [ "--help"]
