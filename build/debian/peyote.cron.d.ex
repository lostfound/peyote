#
# Regular cron jobs for the peyote package
#
0 4	* * *	root	[ -x /usr/bin/peyote_maintenance ] && /usr/bin/peyote_maintenance
