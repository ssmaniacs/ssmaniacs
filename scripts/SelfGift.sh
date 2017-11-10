#!/bin/bash
# vim: ts=4

ADDITEM() {
    ITEM=${1%x*}
    if [[ ${ITEM} == ${1} ]]; then
        CNT=1
    else
        CNT=${1#*x}
    fi

	echo "INSERT INTO gifts(itemid, number) values(${ITEM}, ${CNT});"
}

{
	for i in $*; do
		ADDITEM $i
	done
	cat <<-EOF
		.mode tabs
		.headers on
		select itemid, number from gifts;
	EOF
} | sqlite3 SelfGift.db
