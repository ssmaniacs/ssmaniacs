#!/bin/bash
# vim: ts=4

declare -A items_

LAST=0
while :; do
	UPDATE=$(date -r json/UpdateInventory.req.json +%s)
	if [[ ${UPDATE} -gt ${LAST} ]]; then
		echo $(date +"%Y-%m-%d %H:%M:%S"): Inventory updated
		while read ID NUM; do
			item_[${ID}]=${NUM}
			echo ${ID} = ${item_[${ID}]}
		done < <(./ItemInfo.py ../resources json element | awk '/^[0-9]/{print $1,$3;}')
		sqlite3 SelfGift.db "delete from gifts; delete from inventory"
		./ItemInfo.py ../resources json element | awk '/^[0-9]/{print $1"|"$3;}' > inventory.txt
		sqlite3 SelfGift.db ".import 'inventory.txt' inventory"
	fi

	PENDING=$(sqlite3 SelfGift.db "select count(*) from gifts;")
	if [[ ${PENDING} -ne 0 ]]; then
		sleep 1
		continue
	fi

	LAST=$(date +%s)

	MIN=
    for key in ${!item_[@]}; do
		if [[ -z ${MIN} ]]; then
			MIN=${item_[${key}]}
		elif [[ ${item_[${key}]} -lt ${MIN} ]]; then
			MIN=${item_[${key}]}
		fi
	done

	BASE=$((MIN - 1))
	BASE=$((BASE / 10))
	BASE=$((BASE + 1))
	BASE=$((BASE * 10))

	TOTAL=0
	ARGS=

	while [[ ${TOTAL} -le 290 ]]; do
		echo BASE is ${BASE}
	    for key in ${!item_[@]}; do
			if [[ ${item_[${key}]} -lt ${BASE} ]]; then
				CNT=${item_[${key}]}
				ADD=$((BASE - CNT))

				item_[${key}]=$((CNT + ADD))
				echo ${key} = ${CNT} + ${ADD}

				ARGS="${ARGS} ${key}x${ADD}"
				TOTAL=$((TOTAL + ADD))

				if [[ ${TOTAL} -gt 290 ]]; then
					break
				fi
			fi
		done

		BASE=$((BASE + 10))
	done

	./SelfGiftAdd.sh ${ARGS}

	sqlite3 SelfGift.db "select itemid, count(*), stock from gifts join inventory using (itemid) group by 1, 3;"
	LAST=$(date +%s)
	sleep 1
done
