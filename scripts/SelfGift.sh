#!/bin/bash
# vim: ts=4

DNAT_SRC=192.168.99.100/30
DNAT_DST=68.168.210.28
DNAT_ADDR=192.168.99.1
DNAT_PORT=9999
JSONDIR=${1:-json}
sudo iptables -t nat -A PREROUTING -s ${DNAT_SRC} -d ${DNAT_DST} -p tcp -m tcp --dport 80 -j DNAT --to-destination ${DNAT_ADDR}:${DNAT_PORT}
sudo iptables -t nat -nL | grep ${DNAT_ADDR}
trap "echo Disabling DNAT; sudo iptables -t nat -D PREROUTING -s ${DNAT_SRC} -d ${DNAT_DST} -p tcp -m tcp --dport 80 -j DNAT --to-destination ${DNAT_ADDR}:${DNAT_PORT}" EXIT
set -x; python ./SelfGift.py ${DNAT_PORT} ./${JSONDIR}
