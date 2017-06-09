#!/bin/bash
# convert SecretSociety image files
# - Foreground JPG + Mask JPG -> Transparent PNG
# - Frames PNG -> Each Frame

while [[ $1 ]]; do
	case $1 in
	-v)		VERBOSE=true;;
	test)	TEST=echo;;
	force)	FORCE=true;;
	*)		break;;
	esac
	shift
done

if [[ -f $1 ]]; then
	echo Reading conversion list from $1
	exec < $1
else
	echo Reading conversion list from stdin
fi

CNT=0
while read mode orig mask dest exist; do
	case ${mode} in
	COMBINE)
		if [[ -f ${dest} && ${FORCE} != true ]]; then
			if [[ ${dest} -ot ${orig} ]]; then
				echo COMB ${dest} is older
				#${TEST} mv ${dest} ${dest}.old
			else
				[[ ${VERBOSE} ]] && echo COMB ${dest} is newer
				continue
			fi
		fi

		if [[ ! -d ${dest%/*} ]]; then
			${TEST} mkdir -p ${dest%/*}
		fi

		if [[ ${mask} != '-' ]]; then
			echo JOIN$'\t'${dest}
			${TEST} convert ${orig} ${orig%/*}/${mask} \( -clone 0 -alpha extract \) \
				\( -clone 1 -clone 2 -compose multiply -composite \) \
				-delete 1,2 -alpha off -compose copy_opacity -composite \
				-strip ${dest}

		elif [[ ${orig##*.} == 'png' ]]; then
			echo COPY$'\t'${dest}
			${TEST} convert -strip ${orig} ${dest}

		else
			echo CONV$'\t'${dest}
			${TEST} convert -strip ${orig} ${dest}
		fi
		;;

	CROP)
		dest=${orig%/*}/${dest}
		if [[ -f ${dest} && ${FORCE} != true ]]; then
			if [[ ${dest} -ot ${orig} ]]; then
				echo CROP sed${dest} is older
				# ${TEST} mv ${dest} ${dest}.old
			else
				[[ ${VERBOSE} ]] && echo CROP ${dest} is newer
				continue
			fi
		fi

		echo CROP$'\t'${dest}
		${TEST} convert ${orig} -crop ${mask} -strip ${dest}
		;;

	*)	continue
		;;
	esac

	CNT=$((CNT + 1))
done
