#!/bin/bash

date
appdir=`dirname $0`
logfile=$appdir/plot_HumedadNetwork.log
lockfile=$appdir/plot_HumedadNetwork.lck
pid=$$

echo $appdir

function plot_HumedadNetwork {

python /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/06_Crones/plot_HumedadNetwork.py

}


(
        if flock -n 301; then
                cd $appdir
                plot_HumedadNetwork
                echo $appdir $lockfile
                rm -f $lockfile
        else
            	echo "`date` [$pid] - Script is already executing. Exiting now." >> $logfile
        fi
) 301>$lockfile

exit 0