FROM gauteh/dars:latest

RUN wget -qO- https://repos.influxdata.com/influxdb.key | apt-key add -
RUN echo "deb https://repos.influxdata.com/ubuntu bullseye stable" | tee /etc/apt/sources.list.d/influxdb.list
RUN apt update && apt install -y telegraf && rm -r /var/lib/apt/lists/*
COPY telegraf.conf /etc/telegraf/telegraf.conf

COPY start.sh /bin/start.sh
ENTRYPOINT ["/usr/bin/env"]
CMD ["bash", "start.sh"]