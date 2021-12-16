#!/bin/sh
echo "Starting telegraf..."
telegraf -config /etc/telegraf/telegraf.conf &
echo "Starting dars..."
dars -a 0.0.0.0:80 /data/