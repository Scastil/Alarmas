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
from multiprocessing import Pool

#Nota: las funciones operacionales se ejecutan desde otro .py donde ya se leen sus argumentos. No lee configfile. No cargan simubasin.
# las funciones no operacionales se ejecutan esporadicamente, por tanto leen el configfile para obtener argumentos, y cargan simubasin.
# las funciones base son las que abren directamente el configfile y lidean con rutas.

#---------------
#Funciones base.
#---------------

def get_rutesList(rutas):
    ''' Abre el archivo de texto en la ruta: rutas, devuelve una lista de las lineas de ese archivo.
        Funcion base.
        #Argumentos
        rutas: string, path indicado.
    '''
    f = open(rutas,'r')
    L = f.readlines()
    f.close()
    return L

def get_ruta(RutesList, key):
    ''' Busca en una lista (RutesList) la linea que empieza con el key indicado.
        Funcion base.
        #Argumentos
        RutesList: Lista que devuelve la funcion en este script 'get_rutesList'
        key: string, key indicado para buscar que linea en la lista empieza con el.
    '''
    if any(i.startswith('- **'+key+'**') for i in RutesList):
        for i in RutesList:
            if i.startswith('- **'+key+'**'):
                return i.split(' ')[-1][:-1]
    else:
        return 'Aviso: no existe linea con el key especificado'

def get_tables(RutesList,key):
        ''' Busca en una lista (RutesList) la o las lineas que empieza con el '|'+key indicado y las retorna en otra Lista.
        Se usa para leer infor en tablas especificas.
        Funcion base.
        #Argumentos
        RutesList: Lista que devuelve la funcion en este script 'get_rutesList'
        key: string, key indicado para buscar que linea en la lista empieza con el.
    '''
    List=[]
    for i in RutesList:
            if i.startswith('|'+key) or i.startswith('| '+key):
                List.append(i)
    return List

#-----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------
#Funciones operacionales
#-----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------

#-------------------------------
#Funcion de generacion de lluvia
#-------------------------------

def Rain_Rain2Basin(fechaI,fechaF,hora_1,hora_2,cuenca,rutaNC,rutaRes,Dt=300,umbral=0.005,noextrapol=False,old=False,
                        save_class=False,save_escenarios=False,verbose=True,super_verbose=False):
    ''' #Toma los campos de precipitacion de radar, conv y stratiformes tipo nc y los convierte al formato de la cuenca, esta
        segunda version obtiene tambien los campos con intervalos maximos y minimos de precipitacion. Modificado para incluir
        extrapolacion. 'save_class' y 'save_escenarios' solo se activan cuando 'old' is True, para usarlos se debe crear primero
        los archivos 'rutaRes'+'_stra' - 'rutaRes'+'_conv' y 'rutaRes'+'_low' - 'rutaRes'+'_high'.
        #Funcion operacional.
        #Argumentos:
        fechaI: string, fecha de inicio del periodo.
        fechaF: string, fecha final del periodo.
        cuenca: string, ruta del .nc de la cuenca, debe ser la misma de simulacion.
        rutaNC: string, ruta con los campos de radar historicos generados.
        rutaRes: string, ruta donde guardar los binarios de precip. para esa cuenca.
        Dt: int, delta de t en segundos. Default=300.
        umbral: float, umbral de lluvia minima. Default=0.005
        noextrapol: boolean, no incluir archivos de extrapolacion
        old: bolean, 'True' para cuando el archivo a generar ya existe y se busca actualizarlo y no sobrescribirlo.
        save_class: boolean, crea otros dos archivos de los campos de radar clasificados _conv y _strat
        save_escenarios: boolean, crea otros dos archivos de los escenarios _low y _high de la estimacion de lluvia.
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
        super_verbose:boolean, imprime para cada posicion las imagenes que encontro.
    '''
    
    #Obtiene las fechas por dias
    datesDias = pd.date_range(fechaI, fechaF,freq='D')
    a = pd.Series(np.zeros(len(datesDias)),index=datesDias)
    a = a.resample('A').sum()
    Anos = [i.strftime('%Y') for i in a.index.to_pydatetime()]

    datesDias = [d.strftime('%Y%m%d') for d in datesDias.to_pydatetime()]

    ListDays = []
    ListRutas = []
    for d in datesDias:
        try:
            if noextrapol:
                L = glob.glob(rutaNC + d + '*120.nc')
            else:
                L = glob.glob(rutaNC + d + '*.nc')
            ListRutas.extend(L)
            for i in L:
                if i[-11:].endswith('extrapol.nc'):
                    ListDays.append(i[-32:-20])
                else:
                    ListDays.append(i[-23:-11])
        except:
            print 'mierda'
    #Organiza las listas de dias y de rutas
    ListDays.sort()
    ListRutas.sort()
    datesDias = [dt.datetime.strptime(d[:12],'%Y%m%d%H%M') for d in ListDays]
    datesDias = pd.to_datetime(datesDias)
    #Obtiene las fechas por Dt
    textdt = '%d' % Dt
    #Agrega hora a la fecha inicial
    if hora_1 <> None:
            inicio = fechaI+' '+hora_1
    else:
            inicio = fechaI
    #agrega hora a la fecha final
    if hora_2 <> None:
            final = fechaF+' '+hora_2
    else:
            final = fechaF
    datesDt = pd.date_range(inicio,final,freq = textdt+'s')
    #Obtiene las posiciones de acuerdo al dt para cada fecha
    PosDates = []
    pos1 = [0]
    for d1,d2 in zip(datesDt[:-1],datesDt[1:]):
            pos2 = np.where((datesDias<d2) & (datesDias>=d1))[0].tolist()
            if len(pos2) == 0:
                    pos2 = pos1
            else:
                    pos1 = pos2
            PosDates.append(pos2)
    
    #Carga la cuenca del AMVA
    cuAMVA = cuenca# wmf.SimuBasin(rute = cuenca)
    cuConv = cuenca# wmf.SimuBasin(rute = cuenca)
    cuStra = cuenca# wmf.SimuBasin(rute = cuenca)
    cuHigh = cuenca# wmf.SimuBasin(rute = cuenca)
    cuLow = cuenca# wmf.SimuBasin(rute = cuenca)

    #si el binario el viejo, establece las variables para actualizar
    if old:
        cuAMVA.rain_radar2basin_from_array(status='old',ruta_out= rutaRes)
        if save_class:
            cuAMVA.rain_radar2basin_from_array(status='old',ruta_out= rutaRes + '_conv')
            cuAMVA.rain_radar2basin_from_array(status='old',ruta_out= rutaRes + '_stra')
        if save_escenarios:
            cuHigh.rain_radar2basin_from_array(status='old',ruta_out= rutaRes + '_high')
            cuLow.rain_radar2basin_from_array(status='old',ruta_out= rutaRes + '_low')
    #Itera sobre las fechas para actualizar el binario de campos
    datesDt = datesDt.to_pydatetime()
    print ListRutas[PosDates[0][0]]
    for dates,pos in zip(datesDt[1:],PosDates):
        rvec = np.zeros(cuAMVA.ncells)
        if save_escenarios:
            rhigh = np.zeros(cuAMVA.ncells)
            rlow = np.zeros(cuAMVA.ncells)
        Conv = np.zeros(cuAMVA.ncells, dtype = int)
        Stra = np.zeros(cuAMVA.ncells, dtype = int)
        try:
            for c,p in enumerate(pos):
                #Lee la imagen de radar para esa fecha
                g = netCDF4.Dataset(ListRutas[p])
                RadProp = [g.ncols, g.nrows, g.xll, g.yll, g.dx, g.dx]                        
                #Agrega la lluvia en el intervalo 
                rvec += cuAMVA.Transform_Map2Basin(g.variables['Rain'][:].T/ (12*1000.0), RadProp) 
                if save_escenarios:
                    rhigh += cuAMVA.Transform_Map2Basin(g.variables['Rhigh'][:].T / (12*1000.0), RadProp) 
                    rlow += cuAMVA.Transform_Map2Basin(g.variables['Rlow'][:].T / (12*1000.0), RadProp) 
                #Agrega la clasificacion para la ultima imagen del intervalo
                ConvStra = cuAMVA.Transform_Map2Basin(g.variables['Conv_Strat'][:].T, RadProp)
                Conv = np.copy(ConvStra)
                Conv[Conv == 1] = 0; Conv[Conv == 2] = 1
                Stra = np.copy(ConvStra)
                Stra[Stra == 2] = 0 
                rvec[(Conv == 0) & (Stra == 0)] = 0
                if save_escenarios:
                    rhigh[(Conv == 0) & (Stra == 0)] = 0
                    rlow[(Conv == 0) & (Stra == 0)] = 0
                Conv[rvec == 0] = 0
                Stra[rvec == 0] = 0
                #Cierra el netCDF
                g.close()
        except Exception, e:
            rvec = np.zeros(cuAMVA.ncells)
            if save_escenarios:
                rhigh = np.zeros(cuAMVA.ncells)
                rlow = np.zeros(cuAMVA.ncells)
            Conv = np.zeros(cuAMVA.ncells)
            Stra = np.zeros(cuAMVA.ncells)
        #rvec[ConvStra==0] = 0
        #rhigh[ConvStra==0] = 0
        #rlow[ConvStra==0] = 0
        #Escribe el binario de lluvia
        dentro = cuAMVA.rain_radar2basin_from_array(vec = rvec,
            ruta_out = rutaRes,
            fecha = dates-dt.timedelta(hours = 5),
            dt = Dt,
            umbral = umbral)
        print 'se actualiza'
        if save_escenarios:
            dentro = cuHigh.rain_radar2basin_from_array(vec = rhigh,
                ruta_out = rutaRes+'_high',
                fecha = dates-dt.timedelta(hours = 5),
                dt = Dt,
                umbral = umbral)
            dentro = cuLow.rain_radar2basin_from_array(vec = rlow,
                ruta_out = rutaRes+'_low',
                fecha = dates-dt.timedelta(hours = 5),
                dt = Dt,
                umbral = umbral)
        if dentro == 0: 
            hagalo = True
        else:
            hagalo = False
        #mira si guarda o no los clasificados
        if save_class:
            #Escribe el binario convectivo
            aa = cuConv.rain_radar2basin_from_array(vec = Conv,
                ruta_out = rutaRes+'_conv',
                fecha = dates-dt.timedelta(hours = 5),
                dt = Dt,
                doit = hagalo)
            #Escribe el binario estratiforme
            aa = cuStra.rain_radar2basin_from_array(vec = Stra,
                ruta_out = rutaRes+'_stra',
                fecha = dates-dt.timedelta(hours = 5),
                dt = Dt,
                doit = hagalo)
        #Opcion Verbose
        if super_verbose:
            print dates.strftime('%Y%m%d-%H:%M'), pos

    #Cierrra el binario y escribe encabezado
    cuAMVA.rain_radar2basin_from_array(status = 'close',ruta_out = rutaRes)
    if save_class:
        cuConv.rain_radar2basin_from_array(status = 'close',ruta_out = rutaRes+'_conv')
        cuStra.rain_radar2basin_from_array(status = 'close',ruta_out = rutaRes+'_stra')
    if save_escenarios:
        cuHigh.rain_radar2basin_from_array(status = 'close',ruta_out = rutaRes+'_high')
        cuLow.rain_radar2basin_from_array(status = 'close',ruta_out = rutaRes+'_low')
    #Imprime en lo que va
    if verbose:
            print 'Encabezados de binarios de cuenca cerrados y listos, campos generados en: '
            print rutaRes+'\n'

#-----------------------------------
#-----------------------------------
#Funciones de lectura del configfile
#-----------------------------------
#-----------------------------------

def get_modelPlot(RutesList, PlotType = 'Qsim_map'):
    ''' #Devuelve un diccionario con la informacion de la tabla Plot en el configfile.
        #Funcion operacional.
        #Argumentos:
        - RutesList= lista, es el resultado de leer el configfile con al.get_ruteslist.
        - PlotType= boolean, tipo del plot? . Default= 'Qsim_map'.
    '''
    for l in RutesList:
        key = l.split('|')[1].rstrip().lstrip()
        if key[3:] == PlotType:
            EjecsList = [i.rstrip().lstrip() for i in l.split('|')[2].split(',')]
            return EjecsList
    return key

def get_modelCalib(RutesList):
    ''' #Devuelve un diccionario con la informacion de la tabla Calib en el configfile.
        #Funcion operacional.
        #Argumentos:
        - RutesList= lista, es el resultado de leer el configfile con al.get_ruteslist.
    '''
    DCalib = {}
    for l in RutesList:
        c = [float(i) for i in l.split('|')[3:-1]]
        name = l.split('|')[2]
        DCalib.update({name.rstrip().lstrip(): c})
    return DCalib

def get_modelStore(RutesList):
    ''' #Devuelve un diccionario con la informacion de la tabla Store en el configfile.
        #Funcion operacional.
        #Argumentos:
        - RutesList= lista, es el resultado de leer el configfile con al.get_ruteslist.
    '''
    DStore = {}
    for l in RutesList:
        l = l.split('|')
        DStore.update({l[1].rstrip().lstrip():
            {'Nombre': l[2].rstrip().lstrip(),
            'Actualizar': l[3].rstrip().lstrip(),
            'Tiempo': float(l[4].rstrip().lstrip()),
            'Condition': l[5].rstrip().lstrip(),
            'Calib': l[6].rstrip().lstrip(),
            'BackSto': l[7].rstrip().lstrip(),
            'Slides': l[8].rstrip().lstrip()}})
    return DStore

def get_modelStoreLastUpdate(RutesList):
    ''' #Devuelve un diccionario con la informacion de la tabla Update en el configfile.
        #Funcion operacional.
        #Argumentos:
        - RutesList= lista, es el resultado de leer el configfile con al.get_ruteslist.
    '''
    DStoreUpdate = {}
    for l in RutesList:
        l = l.split('|')
        DStoreUpdate.update({l[1].rstrip().lstrip():
            {'Nombre': l[2].rstrip().lstrip(),
            'LastUpdate': l[3].rstrip().lstrip()}})
    return DStoreUpdate

def get_modelConfig_lines(RutesList, key, Calib_Storage = None, PlotType = None):
    ''' #Devuelve un diccionario con la informacion de las tablas en el configfile: Calib, Store, Update, Plot.
        #Funcion operacional.
        #Argumentos:
        - RutesList= lista, es el resultado de leer el configfile con al.get_ruteslist.
        - key= string, palabra clave de la tabla que se quiere leer. Puede ser: -s,-t.
        - Calib_Storage= string, palabra clave de la tabla que se quiere leer. Puede ser: Calib, Store, Update, Plot.
        - PlotType= boolean, tipo del plot? . Default= None.
    '''
    List = []
    for i in RutesList:
        if i.startswith('|'+key) or i.startswith('| '+key):
            List.append(i)
    if len(List)>0:
        if Calib_Storage == 'Calib':
            return get_modelCalib(List)
        if Calib_Storage == 'Store':
            return get_modelStore(List)
        if Calib_Storage == 'Update':
            return get_modelStoreLastUpdate(List)
        if Calib_Storage == 'Plot':
            return get_modelPlot(List, PlotType=PlotType)
        return List
    else:
        return 'Aviso: no se encuentran lineas con el key de inicio especificado.'

#----------------------------------
#----------------------------------
# Funciones de ejecucion del modelo
#----------------------------------
#----------------------------------

def model_warper(L,verbose=True):
    ''' # Ejecuta directamente el modelo hidrologico de forma operacional para cada paso del tiempo y la proxima media hora,
        para esto: lee el binario de lluvia actual y la extrapolacion, si se programa de tal manera actualiza las CI., corre 
        y genera un archivo con el dataframe de la simulacon de Q en cada nodo para cada paso de tiempo y los binarios del
        estado final de almacenamiento de los tanques (.StObin y .StOhdr) que leera en la proxima ejecucion. Ademas corre y
        genera archivos .bin y .hdr de las celdas deslizadas.
        # Funcion operacional que solo se ejecuta desde la funcion Model_Ejec de alarmas.py.
        # Argumentos:
        -L= lista con tantas listas dentro como numero de parametrizaciones se quieran correr. Dentro debe tener en orden:
        los argumentos de la funcion cu.run_shia(), el nombre de la par. y las rutas de los archivos Ssim y Shist.
        La funcion Model_Ejec se encarga de crear las listas con todo lo necesario para las ejecucion model_warper().
    '''
    #Ejecucion del modelo
    cu=L[11];Rain=L[12];posControl=L[13]
    Res = cu.run_shia(L[1],L[2],L[3],L[4], 
        StorageLoc = L[5], ruta_storage=L[9], kinematicN=12,QsimDataFrame=False)
    #Escribe resultados 
    rutaqsim = L[6]+ L[7] +'_'+L[0].split(' ')[-1]+'.json'
    Qsim = pd.DataFrame(Res['Qsim'][1:].T, 
        index=Rain.index, 
        columns=posControl)
    Qsim.to_json(rutaqsim)
    #Actualiza historico de caudales simulados de la par. asociada.
    rutaqhist = L[8]+ rutaqsim.split('/')[-1].split('.')[0]+'hist.'+rutaqsim.split('/')[-1].split('.')[-1]
    model_write_qhist(rutaqsim,rutaqhist)
    #Se actualizan los historicos de humedad de la parametrizacion asociada.
    model_write_Stohist(L[9],L[10])
    #imprime que ya ejecuto
    if verbose:
        print L[0]+' ejecutado'
    return Res

def Model_Ejec(ruta_out_rain,cuenca,rutaConfig,verbose=True):
    ''' #Setea las ejecuciones del modelo hidrologico con lo dispuesto  en el configfile para cada paso del tiempo.
        #Funcion operacional, pero por estructura interna es mas facil que abra el configfile.
        #Argumentos:
        - ruta_out_rain= string, ruta de la carpeta que contiene los binarios de lluvia, leida antes en el cron.
        - cuenca= simubasin, la cuenca ya leida en el cron.
        - rutaConfig= string, ruta del configfile
        - verbose= boolean, imprime los print de lo que se va ejecutando. Default= True.
    ''' 
    #cuenca
    cu=cuenca
    #se lee el binario de lluvia actual
    rutaRain = ruta_out_rain + 'Lluvia_actual.bin'
    rain_bin, rain_hdr = wmf.__Add_hdr_bin_2route__(rutaRain)
    DataRain = wmf.read_rain_struct(rain_hdr)
    Rain = wmf.read_mean_rain(rain_hdr)
    # se lee el configfile
    ListConfig=get_rutesList(rutaConfig)
    # se leen las rutas de resultados
    #rutas de salida - storage
    ruta_sto = get_ruta(ListConfig, 'ruta_almsim')
    ruta_stohist = get_ruta(ListConfig, 'ruta_almhist')
    #rutas de salida - caudal
    QsimName = get_ruta(ListConfig,'Qsim Name')
    ruta_Qsim = get_ruta(ListConfig, 'ruta_qsim')
    ruta_qhist = get_ruta(ListConfig, 'ruta_qsim_hist')
    #rutas de salida - slides
    ruta_out_slides = get_ruta(ListConfig, 'ruta_slides')
    ruta_slides_bin, ruta_slides_hdr = wmf.__Add_hdr_bin_2route__(ruta_out_slides)

    #Set por defecto de la modelacion
    wmf.models.show_storage = 1
    wmf.models.separate_fluxes = 1
    wmf.models.dt = 300
    wmf.models.sl_fs = 0.5
    wmf.models.sim_slides = 1
    posControl = wmf.models.control[wmf.models.control<>0]

    #Set automatico a partir del configfile
    #Param de configuracion
    Lparam = ['Dt[seg]','Dx[mts]',
        'Almacenamiento medio',
        'Separar Flujos',
        'ruta_almacenamiento',
        'Retorno',
        'Simular Deslizamientos',
        'Factor de Seguridad FS',
        'Factor Corrector Zg']
    DictParam = {}
    for i in Lparam:
        a = get_ruta(ListConfig, i)
        DictParam.update({i:a})

    #Prepara el tiempo y retornos
    wmf.models.dt = float(DictParam['Dt[seg]'])
    wmf.models.retorno = float(DictParam['Retorno'])
    # Prepara los que son binarios (1) si (0) no
    if DictParam['Almacenamiento medio'] == 'True':
        wmf.models.show_storage = 1
    if DictParam['Separar Flujos'] == 'True':
        wmf.models.separate_fluxes = 1
    if DictParam['Simular Deslizamientos'] == 'True':
        wmf.models.sim_slides = 1
        wmf.models.sl_fs = float(DictParam['Factor de Seguridad FS'])
        cu.set_Slides(wmf.models.sl_zs * float(DictParam['Factor Corrector Zg']), 'Zs')
    # print wmf.models.sl_zs.mean()

    #Se leen las calibraciones y la configuracion de actualizar CI.
    DictCalib = get_modelConfig_lines(ListConfig, '-c', 'Calib')
    DictStore = get_modelConfig_lines(ListConfig, '-s', 'Store')

    ############################ EJECUCION ###########################################

    #Prepara las ejecuciones
    ListEjecs = []
    Npasos = DataRain[u' Record'].shape[0]
    for i in DictStore.keys():
        #trata de leer el almacenamiento 
        FileName = glob.glob(ruta_sto + DictStore[i]['Nombre'])
        if len(FileName):
            S = wmf.models.read_float_basin_ncol(ruta_sto+DictStore[i]['Nombre'],1,cu.ncells,5)[0]
        else:
            print 'Error: No se leyeron los binarios de almacenamiento operacionales.'
        #Arma la ejecucion
        Calib = DictCalib[DictStore[i]['Calib']]
        ListEjecs.append([i, Calib, rain_bin, Npasos, 1, S, ruta_Qsim, QsimName,ruta_qhist,ruta_sto+DictStore[i]['Nombre'],ruta_stohist+DictStore[i]['Nombre'][:-7]+'hist.json',cu,Rain,posControl])

    #Ejecucion
    # Cantidad de procesos 
    Nprocess = len(ListEjecs)
    if Nprocess > 15:
        Nprocess = int(Nprocess/1.2)
    #Ejecucion  en paralelo y guarda caudales 
    if verbose:
        print 'Resumen Ejecucion modelo'
        print '\n'
    p = Pool(processes=Nprocess)
    R = p.map(model_warper, ListEjecs)
    p.close()
    p.join()
    #Un brinco para uqe quede lindo el print de deslizamientos.
    if verbose:
        print '\n'
        print 'Resumen deslizamientos'

    ############################ ESCRIBE EL BINARIO DE DESLIZAMIENTOS ##################

    #Archivo plano que dice cuales son las param que simularon deslizamientos 
    f = open(ruta_slides_hdr,'w')
    f.write('## Parametrizaciones Con Simulacion de Deslizamientos \n')
    f.write('Parametrizacion \t N_celdas_Desliza \n')
    #Termina de escribir el encabezado y escribe el binario.
    rec = 0
    for c,i in enumerate(ListEjecs):
        if DictStore[i[0]]['Slides'] == 'True':
            #Determina la cantidad de celdas que se deslizaron
            Slides = np.copy(R[c]['Slides_Map'])
            Nceldas_desliz = Slides[Slides<>0].shape[0]
            f.write('%s \t %d \n' % (i[0], Nceldas_desliz))
            #si esta verbose dice lo que pasa 
            if verbose:
                print 'Param '+i[0]+' tiene '+str(Nceldas_desliz)+' celdas deslizadas.'
            #Escribe en el binario 
            rec = rec+1
            wmf.models.write_int_basin(ruta_out_slides, R[c]['Slides_Map'],rec,cu.ncells,1)
    f.close()    

#-------------------------------
#Funciones de Model_Update_Store
#-------------------------------

def model_update_norain_last(key, ruta_rain_hist, DictUpdate, ruta_bck_sto, ruta_sto, DictStore, date, hours, umbral = 1):
    ''' #Actualiza directamente las CI. del modelo de acuerdo a la condicion estipulada en el configfile.
        #Funcion operacional, usada unicamente por Model_Update_Store.
        #Argumentos:
        -key: string, palabra clave de la tabla
        -ruta_rain_hist: string, ruta del archivo historico de lluvia de la cuenca .hdr.
        -DictUpdate: diccionario, con la informacion de la tabla Update del configfile.
        -ruta_bck_sto: string, ruta de la carpeta que aloja los binarios backsto.
        -ruta_sto: string, ruta de la carpeta que aloja los archivos operacionale de almacenamiento.
        -DictStore: diccionario, con la informacion de la tabla Store del configfile.
        -date: string, fecha de corida del cron. Formato: '%Y-%m-%d-%H:%M:%S'
        -hours: int, numero de horas transcurridas para hacer updates, ledas en el configfile.
        -umbral: float, condicion que debe superarse para hacer update. Default= 1.
    '''
    #lee la lluvia temporal
    rainHist = wmf.read_mean_rain(ruta_rain_hist)
    #condicion
    if hours==0:
        acum=rainHist[-12*hours+rainHist.size:].sum()
    else:
        acum=rainHist[-12*hours:].sum()
    #analiza si se hace update
    if acum < umbral:
        if DictUpdate['-t '+key[3:]]['Nombre'] <> 'None':
            #Remplaza el archivo
            comando = 'cp '+ruta_bck_sto+DictUpdate['-t '+key[3:]]['Nombre']+' '+ruta_sto+DictStore[key]['Nombre']
            os.system(comando)
            #Actualiza la fecha de actualizacion 
            DictUpdate['-t '+key[3:]]['LastUpdate'] = date
            return 0
        else:
            return 1
    else:
        return 1

def model_update_norain_next(key, Rain, DictUpdate,ruta_bck_sto, ruta_sto, DictStore, date, umbral = 1):
    ''' #Actualiza directamente las CI. del modelo de acuerdo a la condicion estipulada en el configfile.
        #Funcion operacional, usada unicamente por Model_Update_Store.
        #Argumentos:
        -key: string, palabra clave de la tabla
        -Rain: pd.Series, con la lectura del .hdr de lluvia_actual.
        -DictUpdate: diccionario, con la informacion de la tabla Update del configfile.
        -ruta_bck_sto: string, ruta de la carpeta que aloja los binarios backsto.
        -ruta_sto: string, ruta de la carpeta que aloja los archivos operacionale de almacenamiento.
        -DictStore: diccionario, con la informacion de la tabla Store del configfile.
        -date: string, fecha de corida del cron. Formato: '%Y-%m-%d-%H:%M:%S'
        -umbral: float, condicion que debe superarse para hacer update. Default= 1.
    '''    
    #Suma la lluvia
    if Rain.sum()<umbral:
        if DictUpdate['-t '+key[3:]]['Nombre'] <> 'None':
            #remplaza
            comando = 'cp '+ruta_bck_sto+DictUpdate['-t '+key[3:]]['Nombre']+' '+ruta_sto+DictStore[key]['Nombre']
            os.system(comando)
            #Actualiza la fecha de actualizacion 
            DictUpdate['-t '+key[3:]]['LastUpdate'] = date
            return 0
        else:
            return 1
    else:
        return 1

def model_update_norain(key, ruta_rain_hist, Rain, DictUpdate, ruta_bck_sto,ruta_sto,DictStore, date, hours, umbral = 1):
    ''' #Actualiza directamente las CI. del modelo de acuerdo a la condicion estipulada en el configfile.
        #Funcion operacional, usada unicamente por Model_Update_Store.
        #Argumentos:
        -key: string, palabra clave de la tabla
        -ruta_rain_hist: string, ruta del archivo historico de lluvia de la cuenca .hdr.
        -Rain: pd.Series, con la lectura del .hdr de lluvia_actual.
        -DictUpdate: diccionario, con la informacion de la tabla Update del configfile.
        -ruta_bck_sto: string, ruta de la carpeta que aloja los binarios backsto.
        -ruta_sto: string, ruta de la carpeta que aloja los archivos operacionale de almacenamiento.
        -DictStore: diccionario, con la informacion de la tabla Store del configfile.
        -date: string, fecha de corida del cron. Formato: '%Y-%m-%d-%H:%M:%S'
        -hours: int, numero de horas transcurridas para hacer updates, leidas en el configfile.
        -umbral: float, condicion que debe superarse para hacer update. Default= 1.
    '''    
    #lee la lluvia temporal
    rainHist = wmf.read_mean_rain(ruta_rain_hist)
    #condicion
    if hours==0:
        acum=rainHist[-12*hours+rainHist.size:].sum()
    else:
        acum=rainHist[-12*hours:].sum()
    #analiza si se hace update
    if acum < umbral and Rain.sum()<umbral:
        if DictUpdate['-t '+key[3:]]['Nombre'] <> 'None':
            #Remplaza
            comando = 'cp '+ruta_bck_sto+DictUpdate['-t '+key[3:]]['Nombre']+' '+ruta_sto+DictStore[key]['Nombre']
            os.system(comando)
            #Actualiza la fecha de actualizacion 
            DictUpdate['-t '+key[3:]]['LastUpdate'] = date
            return 0
        else:
            return 1
    else:
        return 1

def Model_Update_Store(date,rutaRain,ruta_rain_hist,ruta_sto,ruta_bck_sto,DeltaT,DictStore,DictUpdate,rutaConfig,verbose=True):
    ''' # Analiza si actualizar las CI. del modelo de acuerdo a las condiciones estipuladas en el configfile.
        #Funcion operacional que lee el configfile porque dada cierta condicion necesita editarlo.
        #Argumentos:
        -date: string, fecha de corida del cron. Formato: '%Y-%m-%d-%H:%M:%S'
        -rutaRain: string, ruta el .hdr de lluvia_actual.
        -ruta_rain_hist: string, ruta del archivo historico de lluvia de la cuenca .hdr.
        -ruta_sto: string, ruta de la carpeta que aloja los archivos operacionale de almacenamiento.
        -ruta_bck_sto: string, ruta de la carpeta que aloja los binarios backsto.
        -DeltaT: float, lectura del campo del mismo nombre en el configfile.
        -DictStore: diccionario, con la informacion de la tabla Store del configfile.
        -DictUpdate: diccionario, con la informacion de la tabla Update del configfile.
        -ruta_configuracion_1: ruta del configfile.
    '''    
    # lee la lluvia
    rain_bin, rain_hdr = wmf.__Add_hdr_bin_2route__(rutaRain)
    DataRain = wmf.read_rain_struct(rain_hdr)
    Rain = wmf.read_mean_rain(rain_hdr)

    ############################ ACTUALIZACION ###########################################

    #Fecha Actual pasada como parametro
    DateNow = pd.to_datetime(date)
    #Calcula la cantidad de horas desde la ultima actualizacion
    for k in DictUpdate.keys():
        dat = pd.to_datetime(DictUpdate[k]['LastUpdate'])
        deltaT = DateNow - dat
        DictUpdate[k].update({'Horas': deltaT.total_seconds()/3600.0})
    #si la cantidad de horas es inferior al umbral evalua si cumple la 
    #regla establecida 
    for k in DictStore.keys():
        #Evalua si esas condiciones se van a actualizar o no, y si cumplen
        #el tiempo sin ser actualizadas
        if DictStore[k]['Actualizar'] == 'True':
            if DictUpdate['-t '+k[3:]]['Horas'] >= DictStore[k]['Tiempo']:

                #CASO 1: NO RAIN NEXT: No hay lluvia adelante.
                if DictStore[k]['Condition'].split(' ')[0]+' '+DictStore[k]['Condition'].split(' ')[1]+' '+DictStore[k]['Condition'].split(' ')[2] == 'No Rain Next':
                    estado = model_update_norain_next(k, Rain, DictUpdate,ruta_bck_sto, ruta_sto, DictStore, date)

                #CASO 2: NO RAIN LAST: no hay lluvia atras.
                elif DictStore[k]['Condition'].split(' ')[0]+' '+DictStore[k]['Condition'].split(' ')[1]+' '+DictStore[k]['Condition'].split(' ')[2] == 'No Rain Last':
                    #Obtiene las horas de la condicion
                    hours = int(DictStore[k]['Condition'].split(' ')[-2])
                    estado = model_update_norain_last(k, ruta_rain_hist, DictUpdate, ruta_bck_sto, ruta_sto, DictStore, date,hours)

                #CASO 3: NO RAIN: no hay lluvia atras ni adelante.
                elif DictStore[k]['Condition'].split(' ')[0]+' '+DictStore[k]['Condition'].split(' ')[1] == 'No Rain':
                    #Obtiene las horas de la condicion
                    hours = int(DictStore[k]['Condition'].split(' ')[-2])
                    estado = model_update_norain(k,ruta_rain_hist, Rain, DictUpdate, ruta_bck_sto,ruta_sto,DictStore, date,hours)

                #CASO 4: ...

                #si esta diciendo lo que hace dice:
                if verbose:
                    if estado == 0:
                        #Actualiza las fechas dentro del archivo de configuracion 
                        #Lee el archivo de configuracion
                        ListConfig = get_rutesList(rutaConfig)
                        #Obtiene las posiciones en la tabla
                        pos = []
                        key = '-t'
                        for c,i in enumerate(ListConfig):
                            if i.startswith('|'+key) or i.startswith('| '+key):
                                pos.append(c)
                        #Ordena las reglas 
                        Keys = DictUpdate.keys()
                        Keys.sort()
                        #Obtiene las nuevas 
                        for c,p in enumerate(pos):
                            ListConfig[p] = '| '+Keys[c]+'|'+DictUpdate[Keys[c]]['Nombre']+'|'+DictUpdate[Keys[c]]['LastUpdate']+'|\n'
                        #Escribe el nuevo archivo 
                        f = open(rutaConfig,'w')
                        f.writelines(ListConfig)
                        f.close()
                        print 'Aviso: Se han remplazado los estados de: '+k
                    else:
                        print 'Aviso: No se han remplazado los estados de: '+k

#---------------------------------------------------
#Funciones de despligue de resultados y graficacion.
#---------------------------------------------------

def Graph_AcumRain(fechaI,fechaF,cuenca,rutaRain,rutaFigura,vmin=0,vmax=100,verbose=True):
    ''' Genera grafica de acumulado de radar para un periodo especificado, lo plotea y lo guarda en .png
        - Si hay lluvia en el periodo definido devuelve 1 si no 0.
        Funcion operacional.
        #Argumentos
        fechaI: string, fecha de inicio del periodo a acumular.
        fechaF: string, fecha final del periodo a acumular.
        cuenca: string, ruta del .nc de la cuenca sobre la cual acumular, debe ser la misma de simulacion.
        rutaRain: string, ruta con los campos de radar historicos generados para esa cuenca.
        rutaFigura: string, ruta .png donde generar la imagen de acumulado.
        vmin: float o int, valor minimo para pintar los pixeles con el valor acumulado. Default = 0
        vmax: float o int, valor m para pintar los pixeles con el valor acumulado. Default= 100
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
        #Falta poner ventanas mas grandes de pronostico de lluvia ya que el calentamiento con las par y CI actuales
        se toma unos 25 pasos.
    '''
    #Se lee la informacion
    rutebin, rutehdr = wmf.__Add_hdr_bin_2route__(rutaRain)
    cu = cuenca
    DictRain = wmf.read_rain_struct(rutehdr)
    R = DictRain[u' Record']

    #Se cuadran las fechas para que casen con las de los archivos de radar.

    #Se obtienen las fechas con minutos en 00 o 05.
    ####FechaF######
    #Obtiene las fechas por dias
    fecha_f = pd.to_datetime(fechaF)
    fecha_f = fecha_f - pd.Timedelta(str(fecha_f.second)+' seconds')
    fecha_f = fecha_f - pd.Timedelta(str(fecha_f.microsecond)+' microsecond')
    #corrige las fechas
    cont = 0
    while fecha_f.minute % 5 <>0 and cont<10:
        fecha_f = fecha_f - pd.Timedelta('1 minutes')
        cont+=1

    ####FechaI######
    #Obtiene las fechas por dias
    fecha_i = pd.to_datetime(fechaI)
    fecha_i = fecha_i - pd.Timedelta(str(fecha_f.second)+' seconds')
    fecha_i = fecha_i - pd.Timedelta(str(fecha_f.microsecond)+' microsecond')
    #corrige las fechas
    cont = 0
    while fecha_i.minute % 5 <>0 and cont<10:
        fecha_i = fecha_i - pd.Timedelta('1 minutes')
        cont+=1

    #Evalua que las fechas solicitadas existan, si no para aqui y no se grafica nada - if solo sirve para ensayos.. operacionalmente no debe hacer nada.
    try:
        lol=R[fecha_i:fecha_f]

        #Ensaya si las fechas solicitadas cuentan con campo de radar en el binario historico, si no escoge la fecha anterior a esa. Este debe existir tambien, lo ideal es que se mantenga el dt, existan campos cada 5 min.
        ####FechaF######
        Flag = True
        cont = 0
        while Flag:
            try:
                lol = R.index.get_loc(fecha_f)
                Flag = False
            except:
                print 'Aviso: no existe campo de lluvia para fecha_f en la serie entregada, se intenta buscar el de 5 min antes'
                fecha_f = fecha_f - pd.Timedelta('5 minutes')
            cont+=1
            if cont>1:
                Flag = False
        ####FechaI######
        Flag = True
        cont = 0
        while Flag:
            try:
                lol = R.index.get_loc(fecha_i)
                Flag = False
            except:
                print 'Aviso: no existe campo de lluvia para fecha_i en la serie entregada, se intenta buscar el de 5 min antes'
                fecha_i = fecha_i - pd.Timedelta('5 minutes')
            cont+=1
            if cont>1:
                Flag = False

        #Escoge pos de campos con lluvia dentro del periodo solicitado.
        pos = R[fecha_i:fecha_f].values
        pos = pos[pos <>1 ]

        #si hay barridos para graficar
        if len(pos)>0:
            #-------
            #Grafica
            #-------
            #Textos para la legenda
            #~ lab = np.linspace(vmin, vmax, 4)
            #~ texto = ['Bajo', 'Medio', 'Alto', 'Muy alto']
            #~ labText = ['%dmm\n%s'%(i,j) for i,j in zip(lab, texto)]
            #Acumula la lluvia para el periodo
            Vsum = np.zeros(cu.ncells)
            for i in pos:
                v,r = wmf.models.read_int_basin(rutebin,i, cu.ncells)
                v = v.astype(float); v = v/1000.0
                Vsum+=v	
            #Genera la figura 
            c = cu.Plot_basinClean(Vsum, cmap = pl.get_cmap('viridis',10), 
                vmin = vmin, vmax = vmax,#~ show_cbar=True,
                #~ cbar_ticksize = 16,
                #~ cbar_ticks= lab,
                #~ cbar_ticklabels = labText,
                #~ cbar_aspect = 17,
                ruta = rutaFigura,
                figsize = (10,12),show=False)
            # c[1].set_title('Mapa Lluvia de Radar Acumulada', fontsize=16)
            if verbose:
                print 'Aviso: Se ha producido una grafica nueva con valores diferentes de cero en '+rutaFigura
                print fecha_f - fecha_i
            return 1

        #si no hay barridos
        else:
            #-------
            #Grafica
            #-------
            Vsum = np.zeros(cu.ncells)
            c = cu.Plot_basinClean(Vsum, cmap = pl.get_cmap('viridis',10), 
                vmin = vmin, vmax = vmax,#show_cbar=True,
                #~ cbar_ticksize = 16,
                #~ cbar_ticks= lab,
                #~ cbar_ticklabels = labText,
                #~ cbar_aspect = 17,
                ruta = rutaFigura,
                figsize = (10,12),show=False)
            #~ c[1].set_title('Mapa Lluvia de Radar Acumulada', fontsize=16)
            if verbose:
                print 'Aviso: Se ha producido un campo sin lluvia en '+rutaFigura
                print fecha_f - fecha_i
            return 0
    except:
        #si no lo logra que no haga nada.
        print 'Aviso: no se puede construir una serie porque las fechas solicitada no existen, no se genera png de acumulado de '+ str(fecha_f - fecha_i)
        pass

                        
def Plot_qsim_map(Lista,verbose=False):
    #obtiene la razon entre Qsim y Qmed 
    cu=Lista[2]
    qmed = cu.Load_BasinVar('qmed')
    horton = cu.Load_BasinVar('horton')
    cauce = cu.Load_BasinVar('cauce')
    Razon = Lista[-2] / qmed
    #Prepara mapas de grosor y de razon 
    RazonC = np.ones(cu.ncells)
    Grosor = np.ones(cu.ncells)
    for c,i in enumerate([20,50,80,200]):
        for h in range(1,6):        
            camb = 6 - h
            RazonC[(Razon >= i*camb) & (horton == h)] = c+2
            Grosor[(Razon >= i*camb) & (horton == h)] = np.log((c+1)*10)**1.4
    #Plot 
    Coord = cu.Plot_Net(Grosor, RazonC,  
        tranparent = True, 
        ruta = Lista[1],
        clean = True, 
        show_cbar = False, 
        figsize = (10,12), 
        umbral = cauce, 
        escala = 1.5,
        cmap = wmf.pl.get_cmap('viridis',5),
        vmin = None,
        vmax = None,
        show = True)
    #dice lo que hace
    if verbose:
        print 'Aviso: Plot de StreamFlow para '+Lista[-1]+' generado.'

def Graph_Streamflowmap(date,cuenca,ruta_qsim,ruta_sto,ListPlotVar,DictStore,coord=False,record=1,verbose=True):
    #lectura de constantes 
    cu=cuenca
    #construye las listas para plotear en paralelo
    ListaEjec = []
    for l in ListPlotVar:
        ruta_in = ruta_sto + DictStore['-s '+l]['Nombre']
        #Mira la ruta del folder y si no existe la crea
        ruta_folder = ruta_qsim +'-'+l+'/'
        Esta = glob.glob(ruta_folder)
        if len(Esta) == 0:
            os.system('mkdir '+ruta_folder)
        #Obtiene las rutas de los archivos de salida
        ruta_out_png = ruta_folder + 'StreamFlow_'+l+'_'+date+'.png'
        v,r = wmf.models.read_float_basin_ncol(ruta_in,record, cu.ncells, 5)
        ListaEjec.append([ruta_in, ruta_out_png, cu, v[-1], l])

    #Ejecuta los plots
    if len(ListaEjec) > 15:
        Nprocess = 15
    else:
        Nprocess = len(ListaEjec)
    p = Pool(processes = Nprocess)
    p.map(Plot_qsim_map, ListaEjec)
    p.close()

    # #Guarda archuivo con coordenadas
    # if coord:
    #     f = open(ListaEjec[0][2], 'w')
    #     for t,i in zip(['Left', 'Right', 'Bottom', 'Top'], Coord):
    #         f.write('%s, \t %.4f \n' % (t,i))
    #     f.close()

def Plot_Hsim(Lista):
    #Plot
    cu=Lista[2]
    VarToPlot=((Lista[-2][0]+Lista[-2][2])/(wmf.models.max_gravita+wmf.models.max_capilar))*100
    # si supera un umbral de saturacion se grafica, si no no.
    if VarToPlot.max() >= 4:
        bins=4
        ticks_vec=np.arange(0,VarToPlot.max(),int(VarToPlot.max())/bins)
        Coord,ax=cu.Plot_basinClean(VarToPlot,
                        ruta=Lista[1],
                        cmap = pl.get_cmap('viridis',8),
                        figsize = (30,15),
                        # show_cbar=True,
                        # #se configura los ticks del colorbar para que aparezcan siempre la misma cantidad y del mismo tamano
                        # cbar_ticks=ticks_vec,cbar_ticklabels=ticks_vec,cbar_ticksize=15,
                        show=False)
        #ax.set_title('Moisture Map Par'+Lista[-1]+' '+args.date, fontsize=18 )
        # pl.suptitle('Saturacion del suelo [%] Par'+Lista[-1]+' '+args.date, fontsize=16, x=0.5, y=0.09)
        # ax.figure.savefig(Lista[1],bbox_inches='tight')
        print 'Aviso: Plot de Humedad para '+Lista[-1]+' generado.'
    else:
        print 'Aviso: No hay celdas con almenos 4% para Plot de Humedad: max '+str(VarToPlot.max())

def Graph_Moisturemap(date,cuenca,ruta_sto,ruta_Hsim,DictStore,ListPlotVar,coord=False,record=1,verbose=True):
    #Lectura de cuenca y variables
    cu =cuenca
    #construye las listas para plotear en paralelo
    ListaEjec = []
    for l in ListPlotVar:
        #Se define ruta donde se leeran los resultados a plotear
        ruta_in = ruta_sto + DictStore['-s '+l]['Nombre']
        #Se crea un folder en el que se van a contener las imagenes de cada parametrizacion asignada
        #Mira la ruta del folder y si no existe la crea
        ruta_folder = ruta_Hsim+l+'/'
        Esta = glob.glob(ruta_folder)
        if len(Esta) == 0:
            os.system('mkdir '+ruta_folder)
        #Obtiene las rutas de los archivos de salida
        ruta_out_png = ruta_folder +'Humedad'+l+'_'+date+'.png'
        #Lee los binarios de humedad para la cuenca de cada parametrizacion
        v,r = wmf.models.read_float_basin_ncol(ruta_in,record, cu.ncells, 5)
        #Se organiza la lista con parametros necesarios para plotear los mapas con la funcion que sigue
        ListaEjec.append([ruta_in, ruta_out_png, cu, v, l])

    #Ejecuta los plots
    if len(ListaEjec) > 15:
        Nprocess = 15
    else:
        Nprocess = len(ListaEjec)
    p = Pool(processes = Nprocess)
    p.map(Plot_Hsim, ListaEjec)
    p.close()

def Plot_SlidesSim(Lista,verbose=True):
    # #Plots de Parametrizaciones
    # bins=4
    # try:
    # 	ticks_vec=np.arange(0,VarToPlot.max()+1,int(VarToPlot.max())/bins)
    # except:
    # 	ticks_vec=np.arange(0,3.5,0.5)
    
    cu=Lista[2]
    VarToPlot=Lista[-2]
    if Lista[-1] != '999':
        Coord,ax=cu.Plot_basinClean(VarToPlot,#show_cbar=True,
                                    ruta=Lista[1],
                                    cmap = pl.get_cmap('viridis',3),
                                    show=False,figsize = (30,15))                                    
                                #se configura los ticks del colorbar para que aparezcan siempre la misma cantidad y del mismo tamano
                                # cbar_ticks=ticks_vec,cbar_ticklabels=ticks_vec,cbar_ticksize=16,									
        #ax.set_title('Slides Map Par'+Lista[-1]+' '+date, fontsize=16 )
        # pl.suptitle('Slides Map Par'+Lista[-1]+' '+date, fontsize=18, x=0.5, y=0.09)		
        # ax.figure.savefig(Lista[1],bbox_inches='tight')
    #Plot de mapa acumulado de deslizamientos en todas las Parametrizaciones
    else:
        Coord,ax=cu.Plot_basinClean(VarToPlot,#show_cbar=True,
                                    cmap = pl.get_cmap('viridis',3),
                                    ruta=Lista[1],
                                    show=False,figsize = (30,15))                                    
                            #se configura los ticks del colorbar para que aparezcan siempre la misma cantidad y del mismo tamano
                            #~ cbar_ticks=ticks_vec,cbar_ticklabels=ticks_vec,cbar_ticksize=16,
        #ax.set_title('Slides Map AcumPars '+date, fontsize=16 )
        #~ pl.suptitle('Slides Map AcumPars '+date, fontsize=18, x=0.5, y=0.09)
        #~ ax.figure.savefig(Lista[1],bbox_inches='tight')

    #dice lo que hace
    if verbose:
        print 'Aviso: Plot de Deslizamientos para '+Lista[-1]+' generado.'

        
def Graph_Slides(date,cuenca,ruta_in,ruta_out,ListPlotVar,coord=True,verbose=True):
    #Lectura de cuenca y variables
    cu = cuenca
    wmf.models.slide_allocate(cu.ncells, 10)
    #Se marcan con 1 las celdas incondicionalmente inestables.
    R = np.copy(wmf.models.sl_riskvector)
    R1 = np.zeros(cu.ncells)
    pos_ever=np.where(R==2)[1]
    R1[pos_ever] = 1

    #construye las listas para plotear en paralelo para cada parametrizacion
    #Ademas se acumula el numero de celdas acumuladas de todas las parametrizaciones.
    ListaEjec = []; Vsum = np.zeros(cu.ncells)

    for l in range(0,len(ListPlotVar)):
        #Mira la ruta del folder y si no existe la crea
        ruta_folder = ruta_out+ListPlotVar[l]+'/'
        Esta = glob.glob(ruta_folder)
        if len(Esta) == 0:
            os.system('mkdir '+ruta_folder)
        #Obtiene las rutas de los archivos de salida
        ruta_out_png = ruta_folder+'Slides'+ListPlotVar[l]+'_'+date+'.png'
        #Lee los binarios de deslizamientos para la cuenca, para cada parametrizacion
        v,r = wmf.models.read_int_basin(ruta_in,l+1,cu.ncells)
        #Se marcan las celdas simuladas con 2.
        #Si no hay celdas simuladas, deslizamos una para no alterar la escala de colores.
        if v.max()==0:
            v[0]=2
        else:
            v[v==1]=2
        #se suman las celdas siempre inestables con las simuladas
        map1 = R1 + v
        # se  sesga el max a 2 para que se vean bien las celdas simuladas
        map1[map1>2] = 2
        #Se organiza la lista con parametros necesarios para plotear los mapas con la funcion que sigue
        ListaEjec.append([ruta_in, ruta_out_png, cu, map1, ListPlotVar[l]])
        #Se van acumulando las celdas simuladas en cada parametrizacion
        Vsum += v
    #Si marcan las celdas siempre inestables y se sesga a 2 las celdas mayores que 2 para no alterar escala de color.
    Vsum[pos_ever]=1
    Vsum[Vsum>2]=2
    #si no hay celdas deslizadas, deslizamos una para no alterar la escala de colores.
    if Vsum.max()==1:
        Vsum[0]=2
    else:
        pass

    ###Se agrega el mapa de celdas acumuladas entre los que se van a plotear desde la info en ListaEjec
    #Obtiene las rutas de los archivos de salida
    #Mira la ruta del folder y si no existe la crea
    ruta_folder = ruta_out+'ParsAcum/'
    Esta = glob.glob(ruta_folder)
    if len(Esta) == 0:
        os.system('mkdir '+ruta_folder)
    ruta_out_png = ruta_folder+'SlidesParsAcum_'+date+'.png'
    #Se organiza la lista con parametros necesarios para plotear los mapas con la funcion que sigue
    ListaEjec.append([ruta_in, ruta_out_png, cu, Vsum, '999'])

    #Ejecuta los plots
    if len(ListaEjec) > 15:
        Nprocess = 15
    else:
        Nprocess = len(ListaEjec)
    p = Pool(processes = Nprocess)
    p.map(Plot_SlidesSim, ListaEjec)
    p.close()

    #Guarda archuivo con coordenadas - por defecto es false, cuando se cambie revisar Coord.
    # if coord:
    #     f = open(ListaEjec[0][2], 'w')
    #     for t,i in zip(['Left', 'Right', 'Bottom', 'Top'], Coord):
    #         f.write('%s, \t %.4f \n' % (t,i))
    #     f.close()
    
def Graph_Levels(ruta_inQhist,ruta_inQsim,ruta_outLevelspng,ruta_out_rain,date,nodosim,codeest,mediah,ruta_outNsim,res_estadistico,pluvio_out,res_pluvioforecast,estpluvio,verbose=True):
    ''' #Genera graficas para cada nodo en .png comparando Nsims y Nobs y los niveles de riesgo, calculando criterio de
        calibracion Nash-Sutcliffe. Incluye resultado de modelo estadistico de crecida y transito y lluvia promedio en la
        cuenca, radar+extrapolacion y pluvio+pluvio_forecast. Se obtiene Nsim a partir de Qsim, restando la media de Qsim y
        sumando la media historicade Qobs 'mediah'.
        #Funcion operacional.
        #Argumentos:
        ruta_inQhist: string, ruta de donde se lee el Qhist simulado de una parametrizacion. 
        ruta_inQsim: string, ruta de donde se lee el Qsim de una parametrizacion.
        ruta_outLevelspng: string, ruta de la carpeta donde se guardan los .pngs.
        ruta_out_rain: string, ruta de la carpeta de donde se leen los .hdr de los campos de radar de esa cuenca.
        date: string, con la fecha y hora en la que se corre la imagen, esto para el nombre del .png.
        nodosim: lista de int's de los nodos que corresponden con estaciones de nivel para comparar simulado.
        codeest: lista de int's de los codigos de estaciones que corresponden con nodos de simulacion para comparar simulado.
        mediah: lista de int's de las medias historicas de Nobs en las estaciones que corresponden con nodos de simulacion.
        ruta_outNsim: string, ruta donde de la carpeta donde se guardan las series Nsim corregidas con Nobs.
        res_pluvioforecast: string, ruta donde se lee el resultado de pluvio_forecast.
        estpluvio: lista de strings, usada para especificar las estaciones pluvio dentro de la cuenca.
        pluvio_out: boolean, se tienen en cuenta o se eliminan del df resultado de pluvio_forecast las estaciones leidas del
        configfile.
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
        #Nota: 'nodosim', 'codeest' y 'mediah' deben tener el mismo size, y 'estpluvio' debe tener len(size+1). Esto ya que
        las pos hacen referencia a una misma estacion.
    '''
    #Se cambia formato de 
    nodo_ests=np.array([int(nodo) for nodo in nodosim.split(',')])
    code_ests=np.array([int(nodo) for nodo in codeest.split(',')])
    media_hs=np.array([float(nodo) for nodo in mediah.split(',')])
    #est_pluvio dentro de la cuenca
    ests_pluvio=[line.split('|')[1:-1] for line in estpluvio]
    ests_pluvios=pd.DataFrame(ests_pluvio)
    ests_pluvios.columns=ests_pluvios.iloc[0]
    ests_pluvios.index=ests_pluvios['Nivel-cuenca']
    ests_pluvios=ests_pluvios.drop('Nivel-cuenca')
    ests_pluvios=ests_pluvios.drop('-plu',axis=1)
    ests_pluvios=ests_pluvios.drop('Nivel-cuenca',axis=1)
    ests_pluvios.index.name=''

    #Se leen resultados de simulacion de todas las par. para todos los nodos.
    #Leer ultima hora de historico Qsim para cada par.
    rutah=ruta_inQhist+'*.json'
    readh=glob.glob(rutah)
    #Leer las simulacion actual+extrapolacion
    ruta1=ruta_inQsim+'*.json'
    read1=glob.glob(ruta1)
    #Guarda series completas e hist para sacar Nash
    Qhist=[];Qact=[]
    for rqhist,rqsim in zip(np.sort(readh),np.sort(read1)):
        #Q HIST
        dfhist=pd.read_json(rqhist)
        # #crea index para poner nans en faltantes, si los hay.
        # rngindex=pd.date_range(dfhist.index[0],dfhist.index[-1],freq='5min')
        # dfhist=dfhist.reindex(rngindex)
        #ultima hora, 12 pasos de 5 min.
        qhist=dfhist[-12:]
        #hist para sacar Nash, ultima hr del nodo de salida.
        Qhist.append(qhist[nodo_ests[0]][-12:])
        #Q ACT
        dfsim=pd.read_json(rqsim)
        qEst=dfsim
        #ult hr+ extrapolacion
        Qact.append(qhist.append(qEst))

    for nodo,code,media in zip(nodo_ests,code_ests,media_hs):
        #Lee ruta del archivo a guardar, si no existe se crea
        ruta_folder = ruta_outLevelspng+'/'+str(nodo)+'/'
        Esta = glob.glob(ruta_folder)
        if len(Esta) == 0:
            os.system('mkdir '+ruta_folder)
        ruta_out_png = ruta_folder+'LevelsSimNodo'+str(nodo)+'_'+date+'.png' 
        #lee las estaciones pluvio dentr de la cuenca.
        est_pluvio=ests_pluvios['Est_Pluvioadentro'][codeest].split(',')

        #series
        otra = glob.glob(ruta_outNsim)
        if len(otra) == 0:
            os.system('mkdir '+ruta_outNsim)
        #Obtiene las ruta de archivo de salida
        ruta_out_serie = ruta_outNsim+'NSim'+str(code)+'.csv'

        otra = glob.glob(ruta_outNsim)
        if len(otra) == 0:
            os.system('mkdir '+ruta_outNsim)

        #-------------------------------------------------------------------------------------------------------
        #Grafica comparativa de niveles, con escala de colores y backgroud de siata.
        #------------------------------------------------------------------------------------------------------
        fig= pl.figure(figsize=(12,9))
        ax= fig.add_subplot(111)    

        #Grafica de niveles simulados.
        #Colormap
        #-------------------------------------------------------------------------------------------------------
        parameters = np.linspace(0,len(Qact),len(Qact))
        # norm is a class which, when called, can normalize data into the [0.0, 1.0] interval.
        norm = matplotlib.colors.Normalize(
            vmin=np.min(parameters),
            vmax=np.max(parameters))
        #choose a colormap
        c_m =pl.cm.Spectral#nipy_spectral#winter#autumn#summer#PuBuGn
        # create a ScalarMappable and initialize a data structure
        s_m = pl.cm.ScalarMappable(cmap=c_m, norm=norm)
        s_m.set_array([])
        #------------------------------------------------------------------------------------------------------

    #     # Si el nodo tiene estacion instalada
    #     if  nodo in nodo_est:

        #Lluvia
        ruta_hdrp1=ruta_out_rain + 'Lluvia_historica.hdr'
        ruta_hdrp2=ruta_out_rain + 'Lluvia_actual.hdr'
        Phist=wmf.read_mean_rain(ruta_hdrp1,100000000000,0)
        Pextrapol=wmf.read_mean_rain(ruta_hdrp2,100000000000,0) 

        #-------------------------------------------------------------------------------------------------------
        #Consulta a base de datos: Nobs y Ns de alerta'
        #-------------------------------------------------------------------------------------------------------
        #Se usa las fechas de una serie sim para consultar en bd.
        serieN=Qact[0]
        FI=serieN.index.strftime('%Y-%m-%d')[0]
        FF=serieN.index.strftime('%Y-%m-%d')[-1]
        HI=serieN.index[0].strftime('%H:%M')
        HF=serieN.index[-1].strftime('%H:%M')
        # coneccion a bd con usuario operacional
        host   = '192.168.1.74'
        user   = 'siata_Oper'
        passwd = 'si@t@64512_operacional'
        bd     = 'siata'
        #Consulta a tabla estaciones
        Estaciones="SELECT Codigo,Nombreestacion, offsetN,N,action_level,minor_flooding,moderate_flooding,major_flooding  FROM estaciones WHERE codigo=("+str(code)+")"
        dbconn = MySQLdb.connect(host, user,passwd,bd)
        db_cursor = dbconn.cursor()
        db_cursor.execute(Estaciones)
        result = np.array(db_cursor.fetchall())
        #definicion de niveles de alerta y demas.
        nombreest=result[0][1] 
        n1=float(result[0][4])
        n2=float(result[0][5])
        n3=float(result[0][6])
        n4=float(result[0][7])
        #definicion de tipo N para consultar campo.
        tipo=int(result[0][3])
        if tipo == 1:#radar
            niv='ni'
        elif tipo == 0:#ultrasonido
            niv='pr'
        #Consulta a tabla datos
        sql_datos ="SELECT DATE_FORMAT(fecha,'%Y-%m-%d'), DATE_FORMAT(hora, '%H:%i:%s'), (" +str(result[0][2])+"-"+niv+"), calidad FROM datos WHERE cliente = ("+str(code)+") and fecha between '"+FI+"' and '"+FF+"' and hora between '"+HI+"' and '"+HF+"'"
        dbconn = MySQLdb.connect(host, user,passwd,bd)
        db_cursor = dbconn.cursor()
        db_cursor.execute(sql_datos)
        result_data = np.array(db_cursor.fetchall())
        data = pd.DataFrame(result_data)

        #Se organizan consulta en serie de tiempo.

        fe=[data[0][i]+'-'+data[1][i] for i in range(len(data))]; fe=np.array(fe)
        nobs=[float(data[2][i]) for i in range(len(data))];nobs=np.array(nobs)
        calidad=[int(data[3][i]) for i in range(len(data))];calidad=np.array(calidad)
        #se encuentran y eliminan los datos con datetime malos.
        badpos=[];dates=[]
        for i,date in enumerate(fe):
            try:
                dates.append(dt.datetime.strptime(date,'%Y-%m-%d-%H:%M:%S'))
            except:
                badpos.append(i)
        nobs=np.delete(nobs,badpos)
        calidad=np.delete(calidad,badpos)
        # serie
        Nobs=pd.Series(nobs,index=dates)

        #Se corrgie Nobs por calidad
        try:
            Nobs[np.where((calidad!=1)&(calidad!=2))[0]]=np.nan
        except:
            pass
        # Nobs[Nobs>float(offset)]=np.nan
        Nobs[Nobs>600.0]=np.nan

        #Calidad
        grad=50
        for k in range(1,(len(Nobs)-1)):
            d= Nobs[k]
            c= Nobs[k-1]
            e= Nobs[k+1]
            if abs(d-c)>grad and abs(d-e)>grad:
                Nobs[k]=np.nan

        #Poner Qsims en magnitud de Nobservados.
        Nnodo=[]
        for sim in Qact:
            serie_nodo=sim[nodo]
            Nsim=serie_nodo-serie_nodo.mean()+media
            Nnodo.append(Nsim)
        # Se guardan los Nsim para el programa de Mario
        Nsims=pd.DataFrame(np.array(Nnodo).T, index=Nnodo[0].index)
        Nsims.to_csv(ruta_out_serie)

        # Cosas para graficar niveles de riesgo.
        ylim4=n4+(n4*0.2)
        levels=[n1,n2,n3,n4,ylim4]
        lnames=['N1','N2', 'N3', 'N4']
        lcolors=['g','orange','orangered','indigo']

        #plot
        for i in range(0,len(levels)):
            try:
                ax.fill_between(x=[serieN.index[-2],serieN.index[-1]], 
                                y1=[levels[i],levels[i]],
                                y2=[levels[i+1],levels[i+1]], 
                                color = lcolors[i], 
                                alpha = 0.35,
                                label=lnames[i])
            except:
                pass


        #PLOT
        for i,parameter in zip(np.arange(0,len(Nnodo)),parameters):
            #NASH
            nash=wmf.__eval_nash__(Nobs,Nnodo[i])
            ax.plot(Nnodo[i],lw=2.5,linestyle='--', label='P0'+str(i+1)+'- NS:%.2f'%(nash),color=s_m.to_rgba(parameter))
        #Text ans ticks color.
        backcolor='dimgray'  
        #Obs
        ax.plot(Nobs,c='k',lw=3.5, label='Nobs')
        
        #ESTADISTICO
        # se lee la info del pronostico 30m
        f=open(res_estadistico)
        n_pronos=pickle.load(f)
        f.close()

        n_pronos=pd.DataFrame(n_pronos)

        #si la estacion tiene modelo estadistico
        if float(code) in map(int,n_pronos[0]):
            columns=['codigo','n30p25','n30p50','n30p75','Ttop25','Ttop50','Ttop75']
            n_pronos.columns=columns
            n_pronos['codigo']=map(int,n_pronos['codigo'])
            n_pronos.index=n_pronos['codigo']
            n_pronos=n_pronos.drop('codigo',axis=1)
            n_pronos=n_pronos.T
            
            #si los resultados son todos cero porque no esta lloviendo, no hace nada.
            if n_pronos[code].all() == 0:
                pass
            else:
                #n30m
                na=n_pronos[code]['n30p25'];nb=n_pronos[code]['n30p50'];nc=n_pronos[code]['n30p75']
    #             na=75;nb=100;nc=125
                #tto
                ta=n_pronos[code]['Ttop25'];tb=n_pronos[code]['Ttop50'];tc=n_pronos[code]['Ttop75']
    #             ta=20;tb=30;tc=40
                #tiempo
                t1=Nobs.index[-1]+pd.Timedelta(str(ta)+'min');t2=Nobs.index[-1]+pd.Timedelta(str(tb)+'min')
                t3=Nobs.index[-1]+pd.Timedelta(str(tc)+'min')
                xt1=pd.date_range(t1,t3,freq='5min')

                #plot
                ax.fill_between(xt1,na,nc,color='k',alpha=0.17)
                ax.scatter(t2,nb,c='r')
        else:
            pass
        
        ax.set_title('Est. %s. %s ___ Fecha: %s'%(code,nombreest,serieN.index.strftime('%Y-%m-%d')[0]), fontsize=17,color=backcolor)
        ax.set_ylabel('Nivel  $[cm]$', fontsize=17,color=backcolor)
        ax.axvline(x=Nobs.index[-1],lw=2,color='gray',label='Now')

        # Second axis
        #plot
        axAX=pl.gca()
        ax2=ax.twinx()
        ax2AX=pl.gca()
        try:
            #Mean rainfall
            # Busca en Qact la primera pos del obs.
            p1=Phist[Phist.index.get_loc(Qact[0].index[0]):]
            # Busca en Pextrapol la ultima  pos del Pobs
            p2=Pextrapol[Pextrapol.index.get_loc(Phist.index[-1])+1:]
            P=p1.append(p2)
            #Se pasa a mm/h
            P=P*12.0

            #resto del plot
            ax2.fill_between(P.index,0,P,alpha=0.25,color='dodgerblue',lw=0)
            #limites
            ax2AX.set_ylim((0,20)[::-1]) 
        except:
            print 'Aviso: No se grafica Lluvia promedio, no exiten campos para la fecha en el historico'

        try:
            #Se intenta leer la precipitacion media de pluvio, observada mas forecast estadistico escenario medio.
            f = open(res_pluvioforecast+'_cast_normal.rain','r')
            cast_normal = pickle.load(f)
            f.close()

            #Se escogen las estaciones a tener en cuenta del df leido
            if pluvio_out:
                #se eliminan del df la estaciones indicadas, se obtiene el promedio de P dentro de la cuenca.
                Pcastmean_n=cast_normal.drop(est_pluvio,axis=1).T.mean()
            else:
                #se escogen las estaciones dentro de la cuenca y se obtiene promedio.
                Pcastmean_n=cast_normal[est_pluvio].T.mean()

            #si todo valor en el df es cero porque no hay lluvia, no grafica nada
            if (Pcastmean_n.all() == 0).all() == True:
                pass
            else:
                #Plot
                ax2.fill_between(Pcastmean_n.index,0,Pcastmean_n,alpha=0.25,color='k',lw=0)
                ax2AX.set_ylim((0,20)[::-1])
        except:
            print 'Aviso: No se grafica promedio de pluvio forecast.'

        #Formato  resto de grafica.
        ax.tick_params(labelsize=14)
        ax.grid()
        ax.autoscale(enable=True, axis='both', tight=True)
        #setting default color of ticks and edges
        ax.tick_params(color=backcolor, labelcolor=backcolor)
        for spine in ax.spines.values():
            spine.set_edgecolor('gray')
        #color of legend text
        leg = ax.legend(ncol=3,loc=(0.26,-0.255),fontsize=12)
        for text in leg.get_texts():
            pl.setp(text, color = 'dimgray')

        #ylim para la grafica respecto a Nobs.
        ylim=n4+(n4*0.05)
        y_lim=Nobs.mean()*0.5
        ax.set_ylim(y_lim,ylim)

        #Formato resto de grafica - Second axis
        ax2.set_ylabel(u'Precipitacion media - cuenca [$mm$]',size=17,color=backcolor)    
        ax2.tick_params(labelsize=14)
        ax2.tick_params(color=backcolor, labelcolor=backcolor)
        for spine in ax2.spines.values():
            spine.set_edgecolor('gray')
        #Se guarda la figura.
        ax.figure.savefig(ruta_out_png,bbox_inches='tight')

    if verbose:
        print 'Aviso: Plot de niveles generado en '+ruta_out_png

def GraphAnimationsAndDelLast(rutaFiguras,imagenpagina,nfiles=288,verbose=True):
    ''' #Elimina imagenes generadas en la ruta definida si la cantidad sobre pasa el umbral 'nfiles'.
        Genera animacion con las imagenes que se encuentran en la 'rutaFiguras'.
        Si 'imagenpagina'=True, crea o sobreescribe copia de la ultima imagen aparte para el despligue en la pagina de siata.
        #Funcion operacional.
        #Argumentos:
        rutaFiguras: string, ruta de la carpeta con las imagenes con que se quiere crear animacion, borrar o copiar ultima imagen.
        imagenpagina: boolean, True si se quiere crear copia de la ultima imagen.
        nfiles: int, numero de archivos limite a partir del cual borrar.
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
        '''
    #Lista las carpetas que coinciden con la ruta 
    #si es LevelsGraphs, se lee lo de dentro porque es una sola que tiene varias cosas
    if rutaFiguras.split('/')[-1] == 'LevelsGraphs':
        Lista = glob.glob(rutaFiguras+'/*')
    #si no es, se leen desde afuera porque hay varias par.
    else:
        Lista = glob.glob(rutaFiguras+'*')
    #Itera sobre cada carpeta
    for l in Lista:
        # Organiza archivos
        ListTemp = glob.glob(l+'/*')
        ListTemp.sort()
        # Borra lo viejo 
        if len(ListTemp)>= nfiles:
            for i in ListTemp[:-nfiles]:
                os.system('rm '+i)
            if verbose:
                print 'Aviso: Se han dejado solo '+str(nfiles)+' elementos en '+l
        else:
            if verbose:
                print 'Aviso: No hay suficientes archivos para borrar '+str(len(ListTemp))
        #Se copia ultima imagen para la pagina
        if imagenpagina:
            # sino existe la ruta de la animacion la crea
            rutaIpagina=l+'/imagenpagina/'
            Otra= glob.glob(rutaIpagina)
            if len(Otra) == 0:
                os.system('mkdir '+rutaIpagina)
            #copia la ultima imagen para sobreescribirla siempre con el mismo nombre
            pngsort=[i[-3:] for i in ListTemp]
            pngsort=np.array(pngsort)
            pospng=np.where(pngsort=='png')[0]
            try:
                os.system('cp '+ListTemp[pospng[-1]]+' '+rutaIpagina+'imagenpagina.png')
                print 'Aviso: Se copia ultima imagen para la pagina'
            except:
                pass
        else:
            pass
#SE COMENTA LA GENERACION DE ANIMACIONES PORQUE LA PAGINA LO HACE BIEN, HAY QUE CAMBIAR LOS NOMBRES DE LOS ARCHIVOS PARA QUE ESTE FUNCIONE
        # # Sino existe la ruta de la animacion la crea
        # rutaAnimacion=l+'/animation/'
        # Esta= glob.glob(rutaAnimacion)
        # if len(Esta) == 0:
        #     os.system('mkdir '+rutaAnimacion)
        # # Crea la animacion
        # os.system('convert -delay 10 -loop 0 '+l+'/*00.png '+rutaAnimacion+'animation24hr.gif ')
        # print 'Aviso: Animacion generada en '+rutaAnimacion   

def Genera_json(rutaQhist,rutaQsim,ruta_out,verbose=True):
    ''' #Actualiza, o crea si no existe, un .json para desplegar informacion de los caudales simulados en la pagina de SIATA.
        Guarda: Q_actual (del archivo de la ultima corrida), 
                Qmax_ult24h (del hist), Qmax_next1h (del archivo de la ultima corrida), 
                FechaActual (index inicial del archivo de la ultima corrida), 
                Fecha_max_ult24h (index del valor),
                Fecha_max_next1h (index del valor).
        #Funcion operacional.
        #Argumentos:
        rutaQhist: string, ruta de donde se lee el Qhist simulado de una parametrizacion.
        rutaQsim: string, ruta de donde se lee el Qsim (de la ultima corrida) de una parametrizacion.
        ruta_out: string, ruta donde se escribe el .json.
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
    '''
    #Carga los caudales simulados de la parametrizacionn escogida
    #Qsim historico dataframe
    Qhist = pd.read_json(rutaQhist)
    #Qsim actual y next1hr dataframe
    Qsim=pd.read_json(rutaQsim)
    #Se toman los nodos desde Qsim
    Nodos = Qsim.columns.values

    #Genera el Diccionario con los caudales y sus fechas y escribe el json
    superDict={}
    fecha = {}
    Dict = {}
    for n in Nodos:
        Dict.update({str(n):{}})
        #Qsim en la pos 1.
        Dict[str(n)].update({'Qactual': float('%.3f' % Qsim[n][0])})
        # Dict[str(n)].update({'Qmax_ult24h': float('%.3f' % Qhist[n][-288:].max())})
        Dict[str(n)].update({'Qmax_next1h': float('%.3f' % Qsim[n].max())})
        fecha.update({'FechaActual':Qsim[n].index[0].strftime('%Y-%m-%d-%H:%M')})
        # fecha.update({'Fecha_max_ult24h':Qhist[n][-288:].argmax().strftime('%Y-%m-%d-%H:%M')})
        fecha.update({'Fecha_max_next1h':Qsim[n].argmax().strftime('%Y-%m-%d-%H:%M')})
    superDict.update({'Fechas':fecha})
    superDict.update({'Q':Dict})
    esta=glob.glob(ruta_out)
    if len(esta)==0:
        os.system('mkdir '+ruta_out)
    with open(ruta_out+'Qsim.json', 'w') as outfile:
        json.dump(superDict, outfile)
    if verbose:
        print'Aviso: Se actualiza correctamente el .json'

#-----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------
#Funciones no operacionales
#-----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------
#Funciones que crean rutas de archivos historicos
#------------------------------------------------

def model_write_rutesHists(rutaConfig,Qhist=True,Shist=True):
    ''' #Genera archivos vacios para cada parametrizacion cuando no existe historia o si esta quiere renovarse. 
        Si se quiere dejar de crear rutas para alguno de los dos, se debe indicar False. e.g. Shist=False.
        Genera un dataframe con la primera fila de un qsim, ssim.hdr cualquiera, resultado de simulacion de la cuenca de
        interes; la ruta de este archivo debe estar indicado en el configfile.
        #Funcion no operacinal.
        #Argumentos:
        -rutaConfig: string, ruta del configfile.
        -Qhist: boolean, crear un Qhist. Default= True.
        -Shist: boolean, crear un Shist. Default= True.
    '''

    ListConfig = get_rutesList(rutaConfig)

    #Actualiza Qhist
    if Qhist:
        #se lee la ruta donde se va a escribir
        ruta_qhist = get_ruta(ListConfig,'ruta_qsim_hist')
        #se lee el archivo que se va a copiar
        ruta_qsim = get_ruta(ListConfig,'ruta_qsim')
        rutas_qsim=glob.glob(ruta_qsim+'*.json')
        rutaqsim=rutas_qsim[0]
        #se leen los archivos de todas las par para crear Qhist para cada una.
        listrutas_qsim=np.sort(rutas_qsim)

        for i in listrutas_qsim:
            #Se lee el archivo Qsim de donde tomar la primera fila.
            qsim=pd.read_json(rutaqsim)
            Qh=qsim.iloc[[0]]
            nameQhistfile=i.split('/')[-1].split('.')[0]+'hist.'+i.split('/')[-1].split('.')[-1]
            #Pregunta si ya existe y si se quiere sobreescribir
            try:
                Lol = os.listdir(ruta_qhist)
                pos = Lol.index(nameQhistfile)
                flag = raw_input('Aviso: El archivo Qhist: '+nameQhistfile+' ya existe, desea sobre-escribirlo, perdera la historia de este!! (S o N): ')
                if flag == 'S':
                    flag = True
                else:
                    flag = False
            except:
                flag = True
            #Guardado
            if flag:
                Qh.to_json(ruta_qhist+nameQhistfile)
                print 'Aviso: Se crean los Qhist, el archivo Qsim usado para crear las rutas es: '+rutaqsim
            else:
                print 'Aviso: No se crean los Qhist'
    else: 
        print ' Aviso: No se crean archivos Qhist.'

    #Actualiza Shist
    if Shist:
        ruta_shist = get_ruta(ListConfig,'ruta_almhist')
        ruta_ssim = get_ruta(ListConfig,'ruta_almsim')
        rutas_ssim=glob.glob(ruta_ssim+'*.StOhdr')
        rutassim=rutas_ssim[0]
        listrutas_ssim=np.sort(rutas_ssim)

        for j in listrutas_ssim:
            #Se lee el archivo Qsim de donde tomar la primera fila.
            ssim=pd.read_csv(j, header = 4, index_col = 5, parse_dates = True, usecols=(1,2,3,4,5,6))
            Sh=ssim.iloc[[0]]
            nameShistfile=j.split('/')[-1].split('.')[0]+'hist.'+i.split('/')[-1].split('.')[-1]
            #Pregunta si ya existe y si se quiere sobreescribir
            try:
                Lold = os.listdir(ruta_shist)
                pos = Lold.index(nameShistfile)
                flag = raw_input('Aviso: El archivo Shist: '+nameShistfile+' ya existe, desea sobre-escribirlo, perdera la historia de este!! (S o N): ')
                if flag == 'S':
                    flag = True
                else:
                    flag = False
            except:
                flag = True
            #Guardado
            if flag:
                Sh.to_json(ruta_shist+nameShistfile)
                print 'Aviso: Se crean los Shist , el archivo Ssim usado para crear las rutas es: '+rutassim
            else:
                print 'Aviso: No se crean los Shist'
    else: 
        print ' Aviso: No se crean archivos S.'        

def model_write_qhist(rutaQsim,rutaQhist):
    ''' #Actualiza el archivo Qsimhist con el dataframe de la ultima ejecucion de la parametrizacion definida en las rutas de
        entrada. Abre el archivo Qhist y Qsim y hace append del ultimo dato, usa df.reindex(...,freq='5min') para que la
        historia quede organizada cronologicamente, por eso solo funciona si se ejecuta con una frecuencia con minuto = 5.
        La actualizacion de qhist siempre va un paso atras que la de Shist porque el archivo Qsim que genera la ejecucion
        empieza con un paso atras del que corre y el archivo Ssmim no, la actualizacion toma esa primera pos.
        #Funcion operacional.
        #Argumentos:
        -rutaQsim= string, ruta del Qsim
        -rutaQhist= string, ruta del Qhis
    '''
    ##Se actualizan los historicos de Qsim de la parametrizacion asociada.
    #Lee el almacenamiento actual
    Qactual = pd.read_json(rutaQsim)
    #Lee el historico
    Qhist = pd.read_json(rutaQhist)
    #Actualiza Qhist con Qactual.
    try:
        Qhist=Qhist.append(Qactual.iloc[[0]])#.sort_index(axis=1))
        #borra index repetidos, si los hay - la idea es que no haya pero si los hay no funciona el df.reindex
        # Qhist=Qhist.drop_duplicates()
        #Crea el index que debe tener la serie con todos los datos
        rngindex=pd.date_range(Qhist.index[0],Qhist.index[-1],freq='5min')
        #Si hay faltantes los llena, si no deja igual el df. Esto solo funciona cuando dejamos el cron operacional y el 'freq' es exactamente 5 min.
        Qhist=Qhist.reindex(rngindex)
        #Guarda el archivo historico 
        Qhist.to_json(rutaQhist)
        # Aviso
        print 'Aviso: Se ha actualizado el archivo de Qsim_historicos de: '+rutaQhist
    except:
        print 'Aviso: no se esta actualizando Qhist en: '+rutaQhist

def model_write_Stohist(ruta_Ssim,ruta_Shist):
    ''' #Actualiza el Ssimhist con el estado promedio de C.I. de cada tanque, copiandolo desde el .StOhdr a un json antes
        creado.Abre el archivo Shist y Ssim y hace append del ultimo dato, usa df.reindex(...,freq='5min') para que la
        historia quede organizada cronologicamente, por eso solo funciona si se ejecuta con una frecuencia con minuto = 5.
        #Funcion operacional.
        -ruta_Ssim: string, ruta .hdr del archivo de condiciones antecedentes .StObin resultado de la simulacion.
        -ruta_Shist: string, ruta .json del archivo Shist.
    '''
    ##Se actualizan los historicos de humedad de la parametrizacion asociada.
    #Lee el almacenamiento actual
    Sactual = pd.read_csv(ruta_Ssim[:-7]+'.StOhdr', header = 4, index_col = 5, parse_dates = True, usecols=(1,2,3,4,5,6))
    #Lee el historico
    Shist = pd.read_json(ruta_Shist)
    #Actualiza
    Shist=Shist.append(Sactual.iloc[[0]])
    #borra index repetidos, si los hay - la idea es que no haya pero si los hay no funciona el df.reindex
    # Shist=Shist.drop_duplicates()
    # Crea el index que debe tener la serie con todos los datos
    rngindex=pd.date_range(Shist.index[0],Shist.index[-1],freq='5min')
    #Si hay faltantes los llena, si no deja igual el df. Esto solo funciona cuando dejamos el cron operacional y el 'freq' es exactamente 5 min.
    Shist=Shist.reindex(rngindex)

    #guarda el archivo
    Shist.to_json(ruta_Shist)
    print 'Aviso: Se ha actualizado el archivo de Ssim_historicos de: '+ruta_Shist   
    
#------------------------    
#Funciones de graficacion
#------------------------

def Genera_riskvectorMap(rutaConfig,cuenca,figSZ):  
    ''' #Genera un mapa en .png con el risk_vector, esta funcion no es de uso operacional.
        Por lo que necesita leer directamente el ConfigFile.
        #Funcion no operacional.
        #Argumentos:
        - rutaConfig= string, ruta del configfile.
        - cuenca= string, ruta del .nc del simubasin de la cuenca.
        - figSZ= lista, debe tener dos valores dentro de si, x -y del figsize del plot.
    '''
    #Lee el archivo de configuracion
    ListConfig = get_rutesList(rutaConfig)
    #Lectura de rutas de salida de la imagen
    ruta_out = get_ruta(ListConfig,'ruta_map_riskvector')

    #Lectura de cuenca 
    cu = wmf.SimuBasin(rute=cuenca, SimSlides = True)
    wmf.models.slide_allocate(cu.ncells, 10)
    #Mapa risk vector.
    R = wmf.models.sl_riskvector#np.copy(wmf.models.sl_riskvector)
    #Plot
    cu.Plot_basinClean(R,figsize=(figSZ[0],figSZ[1]),cmap = pl.get_cmap('viridis',3),ruta=ruta_out)

#-----------------------------------
#Funciones de edicion del configfile
#-----------------------------------

def write_parameters_on_configfile(rutaConfig,key,add):
    ''' #Agrega o cambia parametros (valores, rutas, etc.) a lineas del configfile que inician con key.
        Esta funcion necesita que siempre exista un ultimo campo despues del key y los dos puntos ':', asi sea un espacio.
        #Funcion no operacional
        #Argumentos:
        - rutaConfig= string, ruta del configfile.
        - key= palabra clabe de la linea a escribir o sobreescribir.
    '''
    #fuente: https://stackoverflow.com/questions/125703/how-to-modify-a-text-file

    #lee archivo con permisos de escritura
    f = open(rutaConfig , 'r+b')   
    f_content = f.readlines()
    #agrega o cambia valores de parametros (valores, rutas, etc.)
    for pos,line in enumerate(f_content):
        if line.startswith('- **'+key+'**'):
            line_now=line
            f_content[pos] = f_content[pos].split(' ')[0]+' '+f_content[pos].split(' ')[1]+' '+add

    # return pointer to top of file so we can re-write the content with replaced string
    f.seek(0)
    # clear file content 
    f.truncate()
    # re-write the content with the updated content
    f.write(''.join(f_content))
    #cierra el archivo
    f.close()
    print 'Aviso: Se edito correctamente la linea **'+key+'** en '+rutaConfig

########################################################################
########################################################################
########################################################################
########################################################################
########################################################################



