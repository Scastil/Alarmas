# #!/bin/bash

# date
# appdir=`dirname $0`
# logfile=$appdir/plotHistory.log
# lockfile=$appdir/plotHistory.lck
# pid=$$

# echo $appdir

# function plotHistory{
#     python /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/06_Crones/plotHistory.py
# }


# (
#         if flock -n 201; then
#                 cd $appdir
#                 plotHistory
#                 echo $appdir $lockfile
#                 rm -f $lockfile
#         else
#                 echo "`date` [$pid] - Script is already executing. Exiting now." >> $logfile
#         fi
# ) 201>$lockfile

# exit 0

#!/bin/bash

date
appdir=`dirname $0`
logfile=$appdir/NombreDelProceso.log
lockfile=$appdir/NombreDelProceso.lck
pid=$$

echo $appdir

function NombreDelProceso {

python /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/06_Crones/plotHistory.py

}


(
        if flock -n 201; then
                cd $appdir
                NombreDelProceso
                echo $appdir $lockfile
                rm -f $lockfile
        else
            	echo "`date` [$pid] - Script is already executing. Exiting now." >> $logfile
        fi
) 201>$lockfile

exit 0