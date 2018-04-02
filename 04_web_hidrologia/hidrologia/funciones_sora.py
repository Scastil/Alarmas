#!/usr/bin/env python
import os 
import pandas as pd
from wmf import wmf
import numpy as np 
import glob 
import pylab as pl
import json
import MySQLdb
import csv
import matplotlib
import matplotlib.font_manager
import datetime as dt
from datetime import timedelta
import datetime as dt
import pickle
import matplotlib.dates as mdates
import netCDF4
import textwrap

def FindMax(Q,fechas,umbral,BusquedaAdelante=36, timedelta='3 hours',frequ='5T'):
    '''Nota: Q debe ser un masked_array'''
    pos=np.where(Q>umbral)[0]
    grupos=[];g=[];Qmax=[]
    #Encuentra el maximo de cada grupo
    for pant,pnext in zip(pos[:-1],pos[1:]):        
        if pant+1>=pnext and pant+BusquedaAdelante>=pnext:
            g.append(pant)
        else:
            if len(g)>0:
                PosMaxGrupo=np.argmax(Q[g])
                grupos.append(g[PosMaxGrupo])
                Qmax.append(np.max(Q[g]))
                g=[]        
    #Pule el maximo por si hay noData
    for c,g in enumerate(grupos):
        if Q.mask[g-1]:
            grupos.pop(c)
    #descarta eventos repetidos.
    Grupos=[]
    for i,ii in enumerate(grupos[:-1]): 
        #ojo con la freq aqui.
        rng=pd.date_range(str(fechas[grupos[i]]-pd.Timedelta(timedelta)),str(fechas[grupos[i]]+pd.Timedelta(timedelta)),freq=frequ)
        #si el sgte esta dentro del rango del anterior, no va.
        if fechas[grupos[i+1]] in rng:
            pass
        else:
            Grupos.append(grupos[i])
    return Grupos

def pdfcdf(serie,bins):
    hr,b = np.histogram(serie,bins)
    hr = hr.astype(float) / hr.sum()
    #hr[hr == 0] = np.nan
    hrc = hr.cumsum()
    b = (b[:-1] + b[1:])/2
    return b,hr,hrc

def hietogram_frombins(Gs_eventos,tipo,years,nameruta):
    ''' Genera una matriz con los hietogramas de los eventos.
        Si tipo <> 'all_cells' se hace con el promedio de las celdas con lluvia.
    '''
    hietogram_0=np.zeros((Gs_eventos.size,73)) #tamano 73 depende del size de pos,ojo.
    for ind,i in  enumerate(Gs_eventos.index):
        serie=[]
        ruta_bin=list(years[nameruta][years[0]==str(i.year)])[0]
        ruta_hdr=list(years[nameruta][years[0]==str(i.year)])[0][:-3]+'hdr'
        #acumulado.
        DictRain = wmf.read_rain_struct(ruta_hdr)
        R = DictRain[u' Record']
        pos=R[i-pd.Timedelta('3 hours'):i+pd.Timedelta('3 hours')].values
        Vsum = np.zeros(cu.ncells)
        for p in pos:
            #se acumula la lluvia de la cuenca
            v,r = wmf.models.read_int_basin(ruta_bin,p,cu.ncells)
            #correcciones de rutina al valor
            v = v.astype(float); v = v/1000.0;v[dicpos['posrare']]=0.0
            #promedio de todas las celdas
            if tipo == 'all_cells':
                serie.append(v.mean())
            #promedio de celdas con lluvia
            elif v.mean()==0.0:
                serie.append(0.0)
            else:     
                serie.append(v[v!=0].mean())
        #se guarda la serie
        hietogram_0[ind]=serie
    return hietogram_0

def getInfoEstaciones(est_codes):
    codeest=est_codes[0]
    # coneccion a bd con usuario operacional
    host   = '192.168.1.74'
    user   = 'siata_Oper'
    passwd = 'si@t@64512_operacional'
    bd     = 'siata'
    #Consulta a tabla estaciones
    Estaciones="SELECT codigo,longitude,latitude,nombreestacion,fechainstalacion  FROM estaciones WHERE codigo=("+str(codeest)+")"
    dbconn = MySQLdb.connect(host, user,passwd,bd)
    db_cursor = dbconn.cursor()
    db_cursor.execute(Estaciones)
    result = np.array(db_cursor.fetchall())
    estaciones_datos_all=pd.DataFrame(result,columns=['codigo','longitud','latitud','nombreestacion','fechainstalacion'])


    for ind,est in enumerate(est_codes[1:]):
        try:
            # codigo de la estacion.
            codeest=est
            # coneccion a bd con usuario operacional
            host   = '192.168.1.74'
            user   = 'siata_Oper'
            passwd = 'si@t@64512_operacional'
            bd     = 'siata'
            #Consulta a tabla estaciones
            Estaciones="SELECT codigo,longitude,latitude,nombreestacion,fechainstalacion  FROM estaciones WHERE codigo=("+str(codeest)+")"
            dbconn = MySQLdb.connect(host, user,passwd,bd)
            db_cursor = dbconn.cursor()
            db_cursor.execute(Estaciones)
            result = np.array(db_cursor.fetchall())
            #holding
            estaciones_datos=pd.DataFrame(result,columns=['codigo','longitud','latitud','nombreestacion','fechainstalacion'])
            estaciones_datos_all=estaciones_datos_all.append(estaciones_datos)
        except:
            pass
    estaciones_datos_all.index=estaciones_datos_all['codigo']
    estaciones_datos_all.index.name=''
    estaciones_datos_all=estaciones_datos_all.drop('codigo',axis=1)
    return estaciones_datos_all