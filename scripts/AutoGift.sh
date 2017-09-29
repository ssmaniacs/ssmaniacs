#!/bin/bash
# vim: ts=4

if [[ $# -ne 1 ]]; then
	echo Usage $0 HHMM
	exit 2
fi

while :; do
	if [[ $(date +%H%M) == $1 ]]; then
		date +"[%Y-%m-%d %H:%M] start auto gifting"
		python ${0%.sh}.py ../resources
		date +"[%Y-%m-%d %H:%M] finished auto gifting"
	fi
	sleep 30
done
