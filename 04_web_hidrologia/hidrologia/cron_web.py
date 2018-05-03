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
rutaN_infoeventos=al.get_ruta(listconfig,'rutaN_infoeventos')
rutaP_infoeventos=al.get_ruta(listconfig,'rutaP_infoeventos')
rutaFigsNbandas=al.get_ruta(listconfig,'rutaFigsNbandas')
rutaFigsPbandas=al.get_ruta(listconfig,'rutaFigsPbandas')
#Lectura del assignfile
dfconfig=pd.read_json(al.get_ruta(listconfig,'ruta_JSONinfosirenas'))

#--------------------------------
#Lectura de resultados de modelos 
#--------------------------------

#Estadistico N
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

#nivel
al.plotN_vs_History(dfconfig,n_pronos,rutaN_infoeventos,rutaFigsNbandas,rng1,timedeltaEv)
#pluvio
al.plotP_vs_History(rutaP_infoeventos,rutaFigsPbandas,cast_normal,rng1,timedeltaEv)