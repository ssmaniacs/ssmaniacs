#!/bin/bash
set -eu

for dir in ../images/*.*; do
	[[ -d ${dir} ]] || continue

	subdir=${dir##*/}
	echo ${subdir}

	[[ -d ../images.lo/${subdir} ]] || mkdir -p ../images.lo/${subdir}

	for img in $(ls -1 ${dir}); do
		[[ -f ../images.lo/${subdir}/${img} ]] || convert -unsharp 12x6+0.5+0 -resize 50% ${dir}/${img} ../images.lo/${subdir}/${img}
	done
done
