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
from datetime import timedelta
import datetime as dt
import pickle
import matplotlib.dates as mdates
import netCDF4
import textwrap

import warnings
warnings.filterwarnings('ignore')

# ########################################################################
# # VARIABLES GLOBALES 

# ruta_store = None
# ruta_store_bck = None

#Nota: las funciones operacionales se ejecutan desde otro .py donde ya se leen sus argumentos. No lee configfile. No cargan simubasin.
# las funciones no operacionales se ejecutan esporadicamente, por tanto leen el configfile para obtener argumentos, y cargan simubasin.
# las funciones base son las que abren directamente el configfile y lidean con rutas.


########################################################################
########################################################################
########################################################################
########################################################################

#FUNCIONES USADAS

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

        #~ #imprime el tamano de lo que esta haciendo 
        #~ if verbose:
            #~ print fecha_f - fecha_i

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
            c[1].set_title('Mapa Lluvia de Radar Acumulada', fontsize=16)
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
    Qhist = pd.read_msgpack(rutaQhist)
    #Qsim actual y next1hr dataframe
    Qsim=pd.read_msgpack(rutaQsim)
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
        Dict[str(n)].update({'Qmax_ult24h': float('%.3f' % Qhist[n][-288:].max())})
        Dict[str(n)].update({'Qmax_next1h': float('%.3f' % Qsim[n].max())})
        fecha.update({'FechaActual':Qsim[n].index[0].strftime('%Y-%m-%d-%H:%M')})
        fecha.update({'Fecha_max_ult24h':Qhist[n][-288:].argmax().strftime('%Y-%m-%d-%H:%M')})
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

def Graph_Levels(ruta_inQhist,ruta_inQsim,ruta_outLevelspng,ruta_out_rain,date,nodosim,codeest,mediah,ruta_outNsim,verbose=True):
    ''' #Genera graficas para cada nodo en .png comparando Nsims y Nobs y los niveles de riesgo, calculando criterio de calibracion
        Nash-Sutcliffe. Se obtiene Nsim a partir de Qsim, restando la media de Qsim y sumando la media historica de Qobs 'mediah'.
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
        verbose: boolean, condicional para que devuelva los prints de la ejecucion. Default= True.
        #Nota: nodosim, codeest y mediah deben tener el mismo size ya que cada pos hace referencia a la misma estacion.
    '''
    #Se cambia formato de 
    nodo_ests=np.array([int(nodo) for nodo in nodosim.split(',')])
    code_ests=np.array([int(nodo) for nodo in codeest.split(',')])
    media_hs=np.array([float(nodo) for nodo in mediah.split(',')])

    #Se leen resultados de simulacion de todas las par. para todos los nodos.
    #Leer ultima hora de historico Qsim para cada par.
    rutah=ruta_inQhist+'*'
    readh=glob.glob(rutah)
    #Leer las simulacion actual+extrapolacion
    ruta1=ruta_inQsim+'_caudal/*'
    read1=glob.glob(ruta1)
    #Guarda series completas e hist para sacar Nash
    Qhist=[];Qact=[]
    for rqhist,rqsim in zip(np.sort(readh),np.sort(read1)):
        if rqhist.endswith('.msg') and rqsim.endswith('.msg'):
            #Q HIST
            dfhist=pd.read_msgpack(rqhist)
            # #crea index para poner nans en faltantes, si los hay.
            # rngindex=pd.date_range(dfhist.index[0],dfhist.index[-1],freq='5min')
            # dfhist=dfhist.reindex(rngindex)
            #ultima hora, 12 pasos de 5 min.
            qhist=dfhist[-12:]
            #hist para sacar Nash, ultima hr del nodo de salida.
            Qhist.append(qhist[nodo_ests[0]][-12:])
            #Q ACT
            dfsim=pd.read_msgpack(rqsim)
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

        #series
        otra = glob.glob(ruta_outNsim)
        if len(otra) == 0:
            os.system('mkdir '+ruta_outNsim)
        #Obtiene las ruta de archivo de salida
        ruta_out_serie = ruta_outNsim+'NSim'+str(code)+'.msg'

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
        Nsims.to_msgpack(ruta_out_serie)

        # Cosas para graficar niveles de riesgo.
        ylim4=n4+(n4*0.2)
        levels=[n1,n2,n3,n4,ylim4]
        lnames=['N1','N2', 'N3', 'N4']
        lcolors=['g','orange','orangered','indigo']

        #plot
        for i in range(0,len(levels)):
            try:
                ax.fill_between(x=[Nobs.index[0],serieN.index[-1]], 
                                y1=[levels[i],levels[i]],
                                y2=[levels[i+1],levels[i+1]], 
                                color = lcolors[i], 
                                alpha = 0.22,
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


    #---------------------------------------------------------------------------
    #CARGADO DE LA CUENCA SOBRE LA CUAL SE REALIZA EL TRABAJO DE OBTENER CAMPOS
    #---------------------------------------------------------------------------
    
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
        
# def Model_Ejec(rutaRain,....cuenca,rutaConfig,newhist,fechai,fechaf,verbose=True):
#     ''' #Ejecuta el modelo hidrologico de forma operacional en cada paso del tiempo y la proxima media hora, para esto: lee el
#         binario de lluvia actual y la extrapolacion, si se programa de tal manera actualiza las CI., corre y genera un archivo con
#         el dataframe de la simulacon de Q en cada nodo para cada paso de tiempo, corre y genera archivos .bin y hdr de las celdas
#         deslizadas.
#         #Funcion operacional.
#         #Argumentos:
#         ----!!!!!!
#     '''

########################################################################
########################################################################
########################################################################
########################################################################

#FUNCIONES NO USADAS

########################################################################
########################################################################
########################################################################
########################################################################

#FUNCIONES FUERA DE alarmas.py O CODIGOS.
# 'Model_Ejec.py '
# 'Model_Update_Store.py '
# 'Graph_StreamFlow_map.py '
# 'Graph_Moisture_map.py '
# 'Graph_Slides_map.py '
########################################################################
# FUNCIONES PARA OBTENER RUTAS 


def get_rain_last_hours(ruta, rutaTemp, hours, DeltaT = 300):
    #calcula los pasos 
    Min = DeltaT/60.0
    MinInHours = 60.0 / Min
    Pasos = int(hours * MinInHours)
    #Escribe la cola de informacion 
    comando = 'tail '+ruta+' -n '+str(Pasos)+' > '+rutaTemp
    os.system(comando)

def get_modelConfig_lines(RutesList, key, Calib_Storage = None, PlotType = None):
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
        return 'Aviso: no se encuentran lineas con el key de inicio especificado'

def get_modelPlot(RutesList, PlotType = 'Qsim_map'):
    for l in RutesList:
        key = l.split('|')[1].rstrip().lstrip()
        if key[3:] == PlotType:
            EjecsList = [i.rstrip().lstrip() for i in l.split('|')[2].split(',')]
            return EjecsList
    return key

def get_modelCalib(RutesList):
    DCalib = {}
    for l in RutesList:
        c = [float(i) for i in l.split('|')[3:-1]]
        name = l.split('|')[2]
        DCalib.update({name.rstrip().lstrip(): c})
    return DCalib

def get_modelStore(RutesList):
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
    DStoreUpdate = {}
    for l in RutesList:
        l = l.split('|')
        DStoreUpdate.update({l[1].rstrip().lstrip():
            {'Nombre': l[2].rstrip().lstrip(),
            'LastUpdate': l[3].rstrip().lstrip()}})
    return DStoreUpdate

########################################################################
# FUNCIONES PARA EDITAR EL CONFIGFILE.

def write_parameters_on_configfile(rutaConfig,key,add):
    '''Agrega o cambia parametros (valores, rutas, etc.) a lineas del configfile que inician con key.
    - rutaConfig: ruta del configfile a editar (ruta en string)
    - key: palabra clave para identificar la linea a editar (una existente dentro del configfile)
    - add: lo que se agrega o cambia en el ultimo elemento de la linea (string). Debe terminar con ' \n'.
    Puede ser vacio (' \n')
    - Esta funcion necesita que siempre exista un ultimo campo despues del key y los dos puntos ':', asi sea un espacio.
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
# FUNCIONES PARA LIDIAR CON CAMPOS DE LLUVIA

def Rain_NoCero(rutaRain):
    f = open(rutarain,'r')
    L = f.readlines()
    f.close()
    return float(L[3].split()[-1])

def Rain_Cumulated(rutaCampo, cu, rutaAcum = None):
    rutabin, rutahdr = wmf.__Add_hdr_bin_2route__(rutaCampo)
    #Lee el esquema del campo 
    D = pd.read_csv(rutahdr,skiprows=5,
        index_col=2, parse_dates=True, 
        infer_datetime_format=True, 
        usecols = (1,2,3))
    Nrecords = D[u' Record'][-1]
    #Acumula la precipitacion para esa consulta
    Vsum = np.zeros(cu.ncells)
    for i in range(1,18):
        v,r = wmf.models.read_int_basin(rutabin,i, cu.ncells)
        v = v.astype(float); v = v/1000.0
        Vsum+=v
    #Entrga Fecha Inicial y Fecha final.
    FechaI = D[u' Record'].index[0]
    FechaF = D[u' Record'].index[-1]
    FechaI = FechaI + pd.Timedelta('5 hours')
    FechaF = FechaF + pd.Timedelta('5 hours')
    #si hay ruta de guardado guarda
    if rutaAcum <> None:
        #Obtiene rutas binaria y hdr
        rutabin, rutahdr = wmf.__Add_hdr_bin_2route__(rutaAcum)
        #Escribe el binario 
        Temp = np.zeros((1, cu.ncells))
        Temp[0] = Vsum
        wmf.models.write_float_basin(rutabin, Temp, 1, cu.ncells, 1)
        #Escribe el encabezado con fecha inicio y fecha fin del binario
        f = open(rutahdr, 'w')
        f.write('Fecha y hora de inicio y fin del binario acumulado:\n')
        f.write('Fecha1: %s\n' % FechaI.to_pydatetime().strftime('%Y%m%d%H%M'))
        f.write('Fecha2: %s\n' % FechaF.to_pydatetime().strftime('%Y%m%d%H%M'))
        f.write('Lluvia Media: %.4f \n' % Vsum.mean())
        f.close()
    return Vsum, FechaI, FechaF

def Rain_Cumulated_Dates(rutaAcum, rutaNC):
    #Obtiene las fechas
    f = open(rutaAcum, 'r')
    L = f.readlines()
    f.close()
    f1 = L[1].split()[1]
    f2 = L[2].split()[1]
    Df = {'Fecha1': L[1].split()[1], 'Fecha2': L[2].split()[1]}
    Df1 = {'Fecha1': {'atras': pd.to_datetime(f1)-pd.Timedelta('30 minutes'),
        'adelante':pd.to_datetime(f1)+pd.Timedelta('30 minutes')},
        'Fecha2': {'atras': pd.to_datetime(f2)-pd.Timedelta('30 minutes'),
        'adelante':pd.to_datetime(f2)+pd.Timedelta('30 minutes')}}
    Fechas = []
    for k in ['Fecha1','Fecha2']:
        #Obtuiene fechas atras y adelante
        f11 = Df1[k]['atras'].to_pydatetime().strftime('%Y%m%d')
        f12 = Df1[k]['adelante'].to_pydatetime().strftime('%Y%m%d')
        #Lista lo que hay alrededor
        List = glob.glob(rutaNC+f11+'*.nc')
        List.extend(glob.glob(rutaNC+f12+'*.nc'))
        List.sort()
        List = np.array([pd.to_datetime(i[43:55]) for i in List])
        #Diferenciass de fecha
        Diff = np.abs(List - pd.to_datetime(Df[k]))
        for i in range(4):
            try:
                Fechas.append(List[Diff.argmin()+i])
            except:
                Fechas.append(pd.to_datetime('200001010000'))
    #Fechas[1] = List[Diff.argmin()+1]
    return Fechas



########################################################################
# FUNCIONES PARA SET DEL MODELO 

def model_get_constStorage(RutesList, ncells):
    Storage = np.zeros((5, ncells))
    for i,c in enumerate(['Inicial Capilar','Inicial Escorrentia','Inicial Subsup','Inicial Subterraneo','Inicial Corriente']):
        Cs = float(get_ruta(RutesList, c))
        Storage[i] = Cs
    return Storage.astype(float)

def model_write_rutesHists(rutaConfig,Qhist=True,Shist=True):
    '''Genera archivos vacios para cada parametrizacion cuando no existe historia o si esta quiere renovarse. 
    Si se quiere dejar de crear rutas para alguno de los dos, se debe indicar False. e.g. Shist=False.
    Genera un dataframe con la primera fila de un qsim, ssim cualquiera, resultado de simuacion de la cuenca de interes'''
    ListConfig = get_rutesList(rutaConfig)
    
    #Actualiza Qhist
    if Qhist:
        ruta_qhist = get_ruta(ListConfig,'ruta_qsim_hist')
        ruta_qsim = get_ruta(ListConfig,'ruta_qsim')
        rutas_qsim=glob.glob(ruta_qsim+'_caudal/*.msg')
        rutaqsim=rutas_qsim[0]
        listrutas_qsim=np.sort(rutas_qsim)
        
        print 'Aviso: el archivo Qsim usado para crear las rutas es: '+rutaqsim
        
        for i in listrutas_qsim:
            #Se lee el archivo Qsim de donde tomar la primera fila.
            qsim=pd.read_msgpack(rutaqsim)
            Qh=qsim.iloc[[0]]
            #Pregunta si esta
            try:
                Lold = os.listdir(i)
                pos = Lold.index(i)
                flag = raw_input('Aviso: El archivo Qhistorico : '+i+' ya existe, desea sobre-escribirlo, perdera la historia de este!! (S o N): ')
                if flag == 'S':
                    flag = True
                else:
                    flag = False
            except:
                flag = True
                print 'Aviso: Se crean los Qhist'
            #Guardado
            if flag:
                Qh.to_msgpack(ruta_qhist+i.split('/')[-1][:-4]+'_hist.msg')
            else:
                print 'Aviso: No se crean los Shist'
    else: 
        print ' Aviso: No se crean archivos Q.'
    #Actualiza Shist
    if Shist:
        ruta_shist = get_ruta(ListConfig,'ruta_almhist')
        ruta_ssim = get_ruta(ListConfig,'ruta_almsim')
        rutas_ssim=glob.glob(ruta_ssim+'*.StOhdr')
        rutassim=rutas_ssim[0]
        listrutas_ssim=np.sort(rutas_ssim)

        print 'Aviso: el archivo Ssim usado para crear las rutas es: '+rutassim

        for j in listrutas_ssim:
            #Se lee el archivo Qsim de donde tomar la primera fila.
            ssim=pd.read_csv(j, header = 4, index_col = 5, parse_dates = True, usecols=(1,2,3,4,5,6))
            Sh=ssim.iloc[[0]]
            #Pregunta si esta
            try:
                Lold = os.listdir(j)
                pos = Lold.index(j)
                flag = raw_input('Aviso: El archivo Shistorico : '+j+' ya existe, desea sobre-escribirlo, perdera la historia de este!! (S o N): ')
                if flag == 'S':
                    flag = True
                else:
                    flag = False
            except:
                flag = True
                print 'Aviso: Se crean los Shist'
            #Guardado
            if flag:
                Sh.to_msgpack(ruta_shist+j.split('/')[-1][:-7]+'_hist.msg')
            else:
                print 'Aviso: No se crean los Shist'
    else: 
        print ' Aviso: No se crean archivos S.'    
    
def model_write_qsim(rutaQsim,rutaQhist, pcont):
    ###Se actualizan los historicos de Qsim de la parametrizacion asociada.
    #Lee el almacenamiento actual
    Qactual = pd.read_msgpack(rutaQsim)
    #Lee el historico
    Qhist = pd.read_msgpack(rutaQhist)
    #Actualiza Qhist con Qactual.
    try:
        Qhist=Qhist.append(Qactual.iloc[[0]])#.sort_index(axis=1))
    except:
        print 'Aviso: no se esta actualizando Qhist en: '+rutaQhist
    #Crea el index que debe tener la serie con todos los datos
    rngindex=pd.date_range(Qhist.index[0],Qhist.index[-1],freq='5min')
    #Si hay faltantes los llena, si no deja igual la funcion.
    Qhist=Qhist.reindex(rngindex)
    # #borra index repetidos, si los hay
    # Qhist=Qhist.drop_duplicates()
    # #Guarda el archivo historico 
    Qhist.to_msgpack(rutaQhist)
    #Aviso
    print 'Aviso: Se ha actualizado el archivo de Qsim_historicos de: '+rutaQhist

def model_write_Stosim(ruta_Ssim,ruta_Shist):
    ''''Actualiza el estado promedio de C.I. de cada tanque, copiandolo desde el .StOhdr a un msg antes creado.
        -ruta_Ssim: ruta .hdr del archivo de condiciones antecedentes .StObin resultado de la simulacion.
        -ruta_Shist: ruta .msg del archivo Shist.'''
    ###Se actualizan los historicos de humedad de la parametrizacion asociada.
    #Lee el almacenamiento actual
    Sactual = pd.read_csv(ruta_Ssim[:-7]+'.StOhdr', header = 4, index_col = 5, parse_dates = True, usecols=(1,2,3,4,5,6))
    #Lee el historico
    Shist = pd.read_msgpack(ruta_Shist)
    #Actualiza
    Shist=Shist.append(Sactual.iloc[[0]])
    #Crea el index que debe tener la serie con todos los datos
    rngindex=pd.date_range(Shist.index[0],Shist.index[-1],freq='5min')
    #Si hay faltantes los llena, si no deja igual la serie
    Shist=Shist.reindex(rngindex)
    # #borra index repetidos, si los hay
    # Shist=Shist.drop_duplicates()
    #guarda el archivo
    Shist.to_msgpack(ruta_Shist)
    print 'Aviso: Se ha actualizado el archivo de Ssim_historicos de: '+ruta_Shist

def model_update_norain():
    print 'no rain'

def model_update_norain_next():
    print 'no next'

def model_update_norain_last(RainRute, Hours):
    # Lee el archivo de lluvia 

    print 'no last'

def model_def_rutes(ruteStore, ruteStoreHist):
    ruta_store = ruteStore
    ruta_store_bck = ruteStoreHist

########################################################################
#FUNCIONES PARA GRAFICAR Y GENERAR RESULTADOS



def Genera_riskvectorMap(rutaConfig,cuenca,figSZ):  
    ''' Genera un mapa en .png con el risk_vector, esta funcion no es de uso operacional.
        Por lo que necesita leer directamente el ConfigFile.'''
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