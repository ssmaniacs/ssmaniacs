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

SUPPLY() {
	MIN=${1:-100}

	while read id type num; do
		#indb=$(sqlite3 SelfGift.db "select count(*) from gifts where itemid=${id};")
		#num=$((num + indb))
		if [[ ${num} -lt ${MIN} ]]; then
			MIN=${num}
		fi
	done  <<EOF
$(./ItemInfo.py ../resource element | tail -n+2)
EOF
	BASE=$((MIN / 10))
	BASE=$((BASE + 1))
	BASE=$((BASE * 10))
	echo Minimum base is ${BASE} >&2

	while read id type num; do
		#indb=$(sqlite3 SelfGift.db "select count(*) from gifts where itemid=${id};")
		#num=$((num + indb))
		if [[ ${num} -lt ${BASE} ]]; then
			ADDITEM ${id}x$((BASE - num))
		fi
	done  <<EOF
$(./ItemInfo.py ../resource element | tail -n+2)
EOF
}

{
	if [[ "$1" == "supply" ]]; then
		SUPPLY $2
	elif [[ "$1" == "quest" ]]; then
		for i in $(./ActiveQuest.py ../resource | awk -F$'\t' '/^[0-9]/{print $4;}'); do
			ADDITEM $i
		done
	elif [[ "$1" == '-' ]]; then
		echo "Input itemids and press Ctrl-D">&2
		while read i; do
			ADDITEM $i
		done
	elif [[ $# -ge 1 ]]; then
		for i in $*; do
			ADDITEM $i
		done
	fi
	cat <<-EOF
		.mode tabs
		.headers on
		select itemid, number from gifts;
	EOF
} | sqlite3 SelfGift.db
