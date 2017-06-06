#!/bin/bash
set -eu

#UNSHARP='-unsharp 12x6+0.5+0'
UNSHARP='-unsharp 0x1'

if [[ $# -ne 2 ]]; then
	echo "Usage: $0 imgdir lo-imgdir"
	exit 2
fi

SRCDIR=$1
DSTDIR=$2

if [[ ! -d $SRCDIR ]]; then
	echo "Directory $SRCDIR does not exist"
	exit 1
fi

mkdir -p $DSTDIR


for dir in $SRCDIR/*.*; do
	[[ -d ${dir} ]] || continue

	subdir=${dir##*/}
	echo ${subdir}

	mkdir -p $DSTDIR/${subdir}

	for img in $(ls -1 ${dir}); do
		dst=$DSTDIR/${subdir}/${img}
		if [[ ${dst} -nt ${dir}/${img} ]]; then
			continue
		elif [[ -f ${dst} ]]; then
			echo ${dst} is older
			# mv ${dst} ${dst}.old
		fi
		convert -resize 50% ${UNSHARP:-} ${dir}/${img} $DSTDIR/${subdir}/${img}
	done
done
