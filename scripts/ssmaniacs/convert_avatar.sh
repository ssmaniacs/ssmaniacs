#!/bin/bash

SRCDIR=../../resources/1024/images/pictures_for_player
DSTDIR=../../docs/img
RESIZE=50x50

mkdir -p ${DSTDIR}

for i in ${SRCDIR}/pic_{1..9}.jpg ${SRCDIR}/pic_??.jpg; do
	DSTFILE=${DSTDIR}/${i##*/}
	if [[ $i -nt ${DSTFILE} ]]; then
		echo converting $i
		convert $i -resize ${RESIZE} ${DSTFILE}
	fi
done
