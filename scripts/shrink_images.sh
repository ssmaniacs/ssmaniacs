#!/bin/bash
set -eu

#UNSHARP='-unsharp 12x6+0.5+0'
UNSHARP='-unsharp 0x1'

for dir in ../images/*.*; do
	[[ -d ${dir} ]] || continue

	subdir=${dir##*/}
	echo ${subdir}

	[[ -d ../images.lo/${subdir} ]] || mkdir -p ../images.lo/${subdir}

	for img in $(ls -1 ${dir}); do
		dst=../images.lo/${subdir}/${img}
		if [[ ${dst} -nt ${dir}/${img} ]]; then
			continue
		elif [[ -f ${dst} ]]; then
			echo ${dst} is older
			mv ${dst} ${dst}.old
		fi
		convert -resize 50% ${UNSHARP:-} ${dir}/${img} ../images.lo/${subdir}/${img}
	done
done
