import numpy as np 
import pandas as pd 
import pylab as pl 
import datetime as dt 
import os 
from wmf import wmf 
from multiprocessing import Pool
import matplotlib
import MySQLdb
import json
from cpr import cpr
import pickle
import alarmas as al
#Ignorar avisos pendejos
import warnings
warnings.filterwarnings('ignore')
import funciones_sora as fs
import glob

date = dt.datetime.now()
dateText = dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

print '\n'
print '###################################### Fecha de Ejecucion: '+dateText+' #############################\n'

#Lectura de ruta de configuracion.
ruta_config= '/media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/configfile_web.md'
listconfig = al.get_rutesList(ruta_config)

#Lectura de rutas
ruta_estadistico=al.get_ruta(listconfig,'ruta_estadistico')
ruta_pluvioforecast=al.get_ruta(listconfig,'ruta_pluvioforecast')
rutaN=al.get_ruta(listconfig,'rutaN_infoeventos')
rutaP=al.get_ruta(listconfig,'rutaP_infoeventos')
rutafigsN=al.get_ruta(listconfig,'rutaFigsNbandas')
rutafigsP=al.get_ruta(listconfig,'rutaFigsPbandas')
#Lectura del assignfile
dfconfig=pd.read_json(al.get_ruta(listconfig,'ruta_JSONinfosirenas'))

#--------------------------------
#Lectura de resultados de modelos 
#--------------------------------

#Estadistico
# se lee la info del pronostico Estadistico 30m
f=open(ruta_estadistico)
n_pronos1=pickle.load(f)
f.close()
n_pronos=pd.DataFrame(n_pronos1)
columns=['codigo','n30p25','n30p50','n30p75','Ttop25','Ttop50','Ttop75']
n_pronos.columns=columns
n_pronos['codigo']=map(int,n_pronos['codigo'])
n_pronos.index=n_pronos['codigo']
n_pronos=n_pronos.drop('codigo',axis=1)
n_pronos=n_pronos.T

#Pluvio Forecast
f = open(ruta_pluvioforecast+'_cast_normal.rain','r')
cast_normal = pickle.load(f)
f.close()



#--------------------
#Ejecucion de figuras
#--------------------

#tick labels for evolution figures
timedeltaEv=5 #min
# label time
hours=np.arange(-3,4)
rng1=[]
for i in range(hours.size):
    if hours[i]<0:
        rng1.append('-0'+str(np.abs(hours[i]))+':00')
    else:
        rng1.append('0'+str(np.abs(hours[i]))+':00')
rng1=np.array(rng1)

#NIVEL

#estaciones.
ests=np.unique(np.hstack(dfconfig['EstNivel']))
ests=ests[np.where(ests)[0]]
# ests_n1=np.hstack(dfconfig['EstNivel1'])
# ests_n1=ests_n1[np.where(ests_n1)[0]]
est_outfig=[246,272,239,173,186,251,259,283,155]

#fechas de consulta nivel.
start=(dt.datetime.now()-pd.Timedelta('3 hours')).strftime('%Y-%m-%d-%H:%M')
end=dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

for est in np.unique(ests):
    if int(est) in est_outfig:
        pass
    else:
        al.plotN_vs_History(int(est),start,end,dfconfig,n_pronos,rutaN,rutafigsN,rng1,timedeltaEv)
        
#PLUVIO

est_noH=[267,281,43 ,261,253]
#se leen las est a plotear
paths_p=glob.glob(rutaP+'bandas*')
ests_p=[i.split('/')[-1].split('_')[-1][:-4] for i in paths_p]
#fechas para consultar pluvio.
start=(dt.datetime.now()-pd.Timedelta('3 days')).strftime('%Y-%m-%d-%H:%M')
end=dt.datetime.now().strftime('%Y-%m-%d-%H:%M')
# for para todas
for est_p in np.sort(ests_p):
    if int(est_p) in est_noH:
        pass
    else:
        al.plotP_vs_History(est_p,start,end,rutaP,rutafigsP,cast_normal,rng1,timedeltaEv)