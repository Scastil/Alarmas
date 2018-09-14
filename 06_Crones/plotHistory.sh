#!/bin/bash

date
appdir=`dirname $0`
logfile=$appdir/plotHistory.log
lockfile=$appdir/plotHistory.lck
pid=$$

echo $appdir

function plotHistory {

python /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/06_Crones/plotHistory.py

}


(
        if flock -n 301; then
                cd $appdir
                plotHistory
                echo $appdir $lockfile
                rm -f $lockfile
        else
            	echo "`date` [$pid] - Script is already executing. Exiting now." >> $logfile
        fi
) 301>$lockfile

exit 0