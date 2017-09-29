#!/bin/bash
# vim: ts=4

SRCDIR=$(cd ../../docs; pwd)

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
	python ${0%.sh}.py ${SRCDIR} list-local.txt ${ROOT} list-${HOST}.txt ${SYNC} > ftpcmd-${HOST}.tmp

	if [[ ! -s ftpcmd-${HOST}.tmp ]]; then
		echo No difference detected

	elif [[ ${CHECK} ]]; then
		cat ftpcmd-${HOST}.tmp

	else
		CWD=$(pwd)

		ftp -nvpi ${HOST} <<-FTP
			user ${USER} ${PASS}
			$(cat ftpcmd-${HOST}.tmp)
			cd /${ROOT}
			lcd ${CWD}
			ls -R list-${HOST}.txt
			bye
		FTP

		echo Re-comparing
		python ${0%.sh}.py ${SRCDIR} list-local.txt ${ROOT} list-${HOST}.txt ${SYNC}
	fi
	rm ftpcmd-${HOST}.tmp
}

if [[ $# -lt 1 ]]; then
	echo "Usage $0 [sync|nosync|check] {webhost|epizy|byethost} [...]"
	exit 2
fi

echo Generating local file list
(cd ${SRCDIR}; find -L . -type f ! -name '*p.json' ! -name '*.zip' -printf "%p %s\n" | sort) > list-local.txt

SYNC=nosync
CHECK=

for k in $*; do
	case $k in
	sync) SYNC=sync
		;;
	nosync) SYNC=nosync
		;;
	check) CHECK=check
		;;
	nocheck) CHECK=
		;;
	webhost)
		upload files.000webhost.com ssmaniacs secretsanta public_html ${SYNC} ${CHECK}
		;;
	xdomain)
		upload sv1.php.xdomain.ne.jp ssmaniacs.php.xdomain.jp secretsanta / ${SYNC} ${CHECK}
		;;
	*)
		echo "Usage $0 ftp-site [{sync|nosync|check|nocheck}] {webhost|xdomain} [...]"
		exit 2
		;;
	esac

done
