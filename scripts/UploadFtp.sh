#!/bin/bash
# vim: ts=4

SRCDIR=$(cd ../docs; pwd)

upload() {
	HOST=$1
	USER=$2
	PASS=$3
	ROOT=$4
	SYNC=$5

	echo Retrieving remote list at ${HOST}
	ftp -npi ${HOST} <<-FTP
		user ${USER} ${PASS}
		cd /${ROOT}
		ls -R list-${HOST}.txt
		bye
	FTP

	echo Comparing
	python ${0%.sh}.py ${SRCDIR} list-local.txt ${ROOT} list-${HOST}.txt ${SYNC} > ftpcmd.tmp

	if [[ ! -s ftpcmd.tmp ]]; then
		echo No difference detected

	elif [[ ${SYNC} == check ]]; then
		cat ftpcmd.tmp

	else
		CWD=$(pwd)

		ftp -nvpi ${HOST} <<-FTP
			user ${USER} ${PASS}
			$(cat ftpcmd.tmp)
			cd /${ROOT}
			lcd ${CWD}
			ls -R list-${HOST}.txt
			bye
		FTP

		echo Re-comparing
		python ${0%.sh}.py ${SRCDIR} list-local.txt ${ROOT} list-${HOST}.txt ${SYNC}
	fi
	rm ftpcmd.tmp
}

if [[ $# -lt 1 ]]; then
	echo "Usage $0 ftp-site [sync|nosync|check] {webhost|epizy|byethost} [...]"
	exit 2
fi

echo Generating local file list
(cd ${SRCDIR}; find -L . -type f -printf "%p %s\n" | sort) > list-local.txt

SYNC=nosync

for k in $*; do
	case $k in
	sync) SYNC=sync
		;;
	nosync) SYNC=nosync
		;;
	check) SYNC=check
		;;
	webhost)
		upload files.000webhost.com ssmaniacs secretsanta public_html ${SYNC}
		;;
	epizy)
		upload ftp.epizy.com epiz_20081221 secretsanta htdocs ${SYNC}
		;;
	byethost)
		upload ftp.byethost7.com b7_20081682 secretsanta htdocs ${SYNC}
		;;
	*)
		echo "Usage $0 ftp-site {webhost|epizy|byethost} [...]"
		exit 2
		;;
	esac

done
