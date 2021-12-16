#!/bin/sh
telegraf -config /etc/telegraf/telegraf.conf &
/entrypoint.sh "$@"