#!/bin/bash
# コレクションアイテムイメージ変換

usage() {
	echo "Usage: $0 resdir imgdir [force]"
	exit 2
}

if [[ $# -lt 2 ]]; then
	usage
fi

SRCDIR=$1/1024/images/items
DSTDIR=$2/items
shift
shift

if [[ ! -d $SRCDIR ]]; then
	echo Directory $SRCDIR does not exist
	exit 1
fi

mkdir -p $DSTDIR

for m in $(find $SRCDIR -type f -name '[1-9]*_.jpg' -printf '%f\n' | sed -nE '/^[0-9]+_\./p' | sort -n); do
	echo COMBINE $SRCDIR/${m%_.jpg}.jpg $SRCDIR/$m $DSTDIR/${m%_.jpg}.png
done
