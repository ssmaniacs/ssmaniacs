#!/bin/bash
# convert SecretSociety image files
# - Foreground JPG + Mask JPG -> Transparent PNG
# - Frames PNG -> Each Frame

if [[ $1 == test ]]; then
	TEST=echo
	shift
fi

if [[ -f $1 ]]; then
	echo Reading conversion list from $1
	exec < $1
else
	echo Reading conversion list from stdin
fi

CNT=0
while read mode orig mask dest exist; do
	if [[ ${exist} || -f ${dest} ]]; then
		#echo EXIST$'\t'${dest}
		continue
	elif [[ ${mode#\#} != ${mode} ]]; then
		continue
	fi

	if [[ ! -d ${dest%/*} ]]; then
		${TEST} mkdir -p ${dest%/*}
	fi

	if [[ ${mode} == 'COMBINE' ]]; then
		if [[ ${mask} != '-' ]]; then
			echo JOIN$'\t'${dest}
			${TEST} convert ${orig} ${mask} \( -clone 0 -alpha extract \) \
				\( -clone 1 -clone 2 -compose multiply -composite \) \
				-delete 1,2 -alpha off -compose copy_opacity -composite ${dest}

		elif [[ ${orig##*.} == 'png' ]]; then
			echo COPY$'\t'${dest}
			${TEST} cp ${orig} ${dest}

		else
			echo CONV$'\t'${dest}
			${TEST} convert ${orig} ${dest}
		fi

	elif [[ ${mode} == 'CROP' ]]; then
		echo CROP$'\t'${dest}
		${TEST} convert ${orig} -crop ${mask} ${dest}
	fi

	CNT=$((CNT + 1))
	#[[ ${CNT} -ge 10 ]] && break
done
