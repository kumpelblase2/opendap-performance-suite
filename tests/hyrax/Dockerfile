FROM opendap/hyrax:latest

COPY influxdb.repo /etc/yum.repos.d/influxdb.repo

RUN set -e \
    && yum -y install \
            telegraf \
    && yum clean all 

COPY telegraf.conf /etc/telegraf/telegraf.conf
COPY start.sh /bin/start.sh

ENTRYPOINT ["/usr/bin/env"]
CMD ["bash", "start.sh", "-"]