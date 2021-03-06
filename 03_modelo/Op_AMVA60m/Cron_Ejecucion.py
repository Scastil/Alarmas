
#!/usr/bin/env python
import pandas as pd 
import datetime as dt 
import os 
from wmf import wmf
from multiprocessing import Pool
import numpy as np
import pickle 
import alarmas as al
import glob 
import time
import pylab as pl
import json
import warnings
warnings.filterwarnings('ignore')

# Texto Fecha: el texto de fecha que se usa para guardar algunos archivos de figuras.
date = dt.datetime.now()
dateText = dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

print '\n'
print '###################################### Fecha de Ejecucion: '+dateText+' #############################\n'

#Lee el archivo de configuracion
ruta_configuracion_1 = '/media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/configfile.md'
RutasList = al.get_rutesList(ruta_configuracion_1)

# Lee rutas de objetos de entrada
ruta_cuenca = al.get_ruta(RutasList, 'ruta_cuenca')
ruta_campos = al.get_ruta(RutasList, 'ruta_campos')
# Lee rutas de salida - lluvia radar
ruta_out_rain = al.get_ruta(RutasList, 'ruta_rain')
ruta_out_rain_png = al.get_ruta(RutasList, 'ruta_rain_png')

############################################## Se carga la cuenca ########################################################
cuenca = wmf.SimuBasin(rute = ruta_cuenca, SimSlides = True)
##########################################################################################################################

#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

print '###################################### CONSULTA DE LA LLUVIA Y EXTRAPOLACION ############################\n'

#-------------------------------------------------------------------
#GENERA EL CAMPO DE LLUVIA DE LOS ULTIMOS 10MIN Y LOS PROXIMOS 60
#-------------------------------------------------------------------
# Obtiene el datetime 
fecha_1 =  date + dt.timedelta(hours = 5) - dt.timedelta(minutes = 10)
fecha_2 =  date + dt.timedelta(hours = 5) + dt.timedelta(minutes = 60) 
# Lo convierte en texto 
fecha1 = fecha_1.strftime('%Y-%m-%d')
fecha2 = fecha_2.strftime('%Y-%m-%d')
hora_1 = fecha_1.strftime('%H:%M')
hora_2 = fecha_2.strftime('%H:%M')
#ruta de bin de lluvia actual
lluvia_actual = ruta_out_rain + 'Lluvia_actual'

# Ejecuta para obtener el campo de lluvia de los ultimos 10 min y de la proxima hora 
al.Rain_Rain2Basin(fecha1,fecha2,hora_1,hora_2,cuenca,ruta_campos,lluvia_actual)

# #-------------------------------------------------------------------
# #ACTUALIZA EL CAMPO DE LLUVIA HISTORICO DE LA CUENCA 
# #-------------------------------------------------------------------
# #Fechas de inicio y fin 
# fecha_1 =  date + dt.timedelta(hours = 5) - dt.timedelta(minutes = 5)
# fecha_2 =  date + dt.timedelta(hours = 5) + dt.timedelta(minutes = 0)
# # Lo convierte en texto 
# fecha1 = fecha_1.strftime('%Y-%m-%d')
# fecha2 = fecha_2.strftime('%Y-%m-%d')
# hora_1 = fecha_1.strftime('%H:%M')
# hora_2 = fecha_2.strftime('%H:%M')
# #Luvia historica 
# lluvia_historica = ruta_out_rain + 'Lluvia_historica'

# # Ejecuta para actualizar el campo de lluvia 
# al.Rain_Rain2Basin(fecha1,fecha2,hora_1,hora_2,cuenca,ruta_campos,lluvia_historica,old=True)

# #-------------------------------------------------------------------
# #GENERA GRAFICAS DE CAMPOS
# #-------------------------------------------------------------------
# fecha2 = date.strftime('%Y-%m-%d-%H:%M')

# print 'Aviso: Se generan graficas de radar para los intervalos:'

# # Grafica de la lluvia en los ultimos 3 dias 
# fecha1 = date - dt.timedelta(hours = 72)
# fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
# ruta_figura = ruta_out_rain_png + 'Acumulado_3dias.png'
# r3dias=al.Graph_AcumRain(fecha1,fecha2,cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=80)

# # Grafica de la lluvia en los ultimas 24 horas
# fecha1 = date - dt.timedelta(hours = 24)
# fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
# ruta_figura = ruta_out_rain_png + 'Acumulado_1dia.png'
# r1dia=al.Graph_AcumRain(fecha1,fecha2,cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=80)

# # Grafica en la ultima hora.
# fecha1 = date - dt.timedelta(hours = 1)
# fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
# ruta_figura = ruta_out_rain_png + 'Acumulado_1hora.png'
# r1hr=al.Graph_AcumRain(fecha1,fecha2,cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=10)

# #Grafica en los proximos 30min
# fecha1 = fecha2
# fecha2= date + dt.timedelta(minutes = 30)
# fecha2 = fecha2.strftime('%Y-%m-%d-%H:%M')
# ruta_figura = ruta_out_rain_png + 'Acumulado_30siguientes.png'
# r30minnext=al.Graph_AcumRain(fecha1,fecha2,cuenca,lluvia_actual,ruta_figura,vmin=0,vmax=20)


# #|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# #|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

# print '###################################### EJECUCION DEL MODELO ############################\n'

# # Se ejectura el modelo con la lluvia de los 5 min corrientes y la proxima hora.

# #-----------------------------------------------------
# #Ejecucion del modelo en el ultimo intervalo de tiempo
# #-----------------------------------------------------

# al.Model_Ejec(ruta_out_rain,cuenca,ruta_configuracion_1)

# #-------------------------------------
# #Actualiza las condiciones del modelo 
# #-------------------------------------
# print ' Actualizaciones de CI.'
# print '\n'
# rutaRain=lluvia_actual+'.bin'
# ruta_rain_hist = al.get_ruta(RutasList, 'ruta_rainHistoryFile')
# ruta_sto = al.get_ruta(RutasList, 'ruta_almsim')
# ruta_bck_sto = al.get_ruta(RutasList, 'ruta_bkc_alm')
# DeltaT = float(al.get_ruta(RutasList, 'Dt[seg]'))
# #Lista de calibraciones
# DictStore = al.get_modelConfig_lines(RutasList, '-s', 'Store')
# DictUpdate = al.get_modelConfig_lines(RutasList, '-t', 'Update')
# al.Model_Update_Store(dateText,rutaRain,ruta_rain_hist,ruta_sto,ruta_bck_sto,DeltaT,DictStore,DictUpdate,ruta_configuracion_1)
# print '\n'
# #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# #  #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# print '\n'
# print '###################################### PRODUCCION DE FIGURAS Y RESULTADOS ############################\n'

# # Para esta cuenca se ejecutan figuras siempre para mostrar los resultados en la pagina de SIATA


# #Actualiza json con los caudaes simulados de la parametrizacion escogida para mostrar en la pagina

# #Se define ruta sin extension del Qhist de la parametrizacion a incluir
# ruta_qhistJson = al.get_ruta(RutasList,'ruta_qhist2Json')
# #Se define ruta sin extension del Qsim de la parametrizacion a incluir
# ruta_qsimJson = al.get_ruta(RutasList,'ruta_qsim2Json')
# #Se define la ruta donde se escribe el Json.
# ruta_outJson = al.get_ruta(RutasList,'ruta_Json')
# #JSON
# al.Genera_json(ruta_qhistJson,ruta_qsimJson,ruta_outJson)

# #--------------------------------------------------
# #Figura de la evolucion de los caudales en el cauce
# #--------------------------------------------------

# #Lectura de rutas
# ruta_qsim = al.get_ruta(RutasList,'ruta_map_qsim')
# ruta_sto = al.get_ruta(RutasList,'ruta_almsim')
# #Dicctionario con info de plot
# ListPlotVar = al.get_modelConfig_lines(RutasList, '-p', Calib_Storage='Plot',PlotType='Qsim_map')

# ListaEjec = []
# for i in range(13):
#     fechaNueva = date + dt.timedelta(minutes = 5*i)
#     fechaNueva = fechaNueva.strftime('%Y-%m-%d-%H:%M')
#     al.Graph_Streamflowmap(fechaNueva,cuenca,ruta_qsim,ruta_sto,ListPlotVar,DictStore,coord=False,record=1,verbose=True)
# print '\n'
# print 'Se ejecutan figuras con mapa de StreamFlow'
# print '\n'

# #Ruta donde se borraran graficas viejas
# ruta_erase_png = al.get_ruta(RutasList, 'ruta_map_qsim')
# #Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen 
# al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)

# #--------------------------------------------------
# #Figura de la humedad simulada en el tiempo actual
# #--------------------------------------------------

# ListPlotVar = al.get_modelConfig_lines(RutasList, '-p', Calib_Storage='Plot',PlotType='Humedad_map')
# #Se define ruta donde se leeran los resultados a plotear
# ruta_sto = al.get_ruta(RutasList,'ruta_almsim')
# #Lectura de rutas de salida de la imagen
# ruta_Hsim = al.get_ruta(RutasList,'ruta_map_humedad')
# #ejecucion
# al.Graph_Moisturemap(dateText,cuenca,ruta_sto,ruta_Hsim,DictStore,ListPlotVar)
# print '\n'
# print 'Se ejecutan figuras con mapa de Humedad'
# print '\n'

# #Ruta donde se borraran graficas viejas
# ruta_erase_png = al.get_ruta(RutasList, 'ruta_map_humedad')
# #Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
# al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)

# #-------------------------------------------------------------------
# #Figura de los deslizamiento simuados en el tiempo acumulado - 5 min.
# #-------------------------------------------------------------------

# ruta_in = al.get_ruta(RutasList,'ruta_slides')
# #Lectura de rutas de salida de la imagen
# ruta_out = al.get_ruta(RutasList,'ruta_map_slides')
# #Diccionario con info de plot: se lee la info de todos los parametrizaciones
# ListPlotVar = al.get_modelConfig_lines(RutasList, '-p', Calib_Storage='Plot',PlotType='Slides')
# #se ejuta
# al.Graph_Slides(dateText,cuenca,ruta_in,ruta_out,ListPlotVar)
# print '\n'
# print 'Se ejecutan figuras con mapa de Deslizamientos'
# print '\n'

# #Ruta donde se borraran graficas viejas
# ruta_erase_png = al.get_ruta(RutasList, 'ruta_map_slides')
# #Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
# al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)

# #----------------------------------------------------------------------
# #Figura comparativa de niveles simulados vs. observado y los de alerta.
# #----------------------------------------------------------------------

# #Se define ruta de donde se leeran los resultados a plotear
# ruta_inQhist = al.get_ruta(RutasList,'ruta_qsim_hist')
# ruta_inQsim = al.get_ruta(RutasList,'ruta_qsim')
# #se leen cosas necesarias para la funcion
# nodosim = al.get_ruta(RutasList,'nodosim')
# codeest = al.get_ruta(RutasList,'codeestN')
# mediah = al.get_ruta(RutasList,'mediaN')
# #Lectura de rutas de salida de la imagen
# ruta_outLevelspng = al.get_ruta(RutasList,'ruta_levelspng')
# #Lectura de rutas donde guardar Nsim.
# ruta_outNsim = al.get_ruta(RutasList,'ruta_niveles')
# #lectura de ruta de los resultados del estadistico
# res_estadistico=al.get_ruta(ConfigFile,'ruta_estadistico')
#lectura de rutas y parametros de los resultados del pluvio_forecast
# res_pluvioforecast=al.get_ruta(ConfigFile,'ruta_pluvioforecast')
# pluvio_out=al.get_ruta(ConfigFile,'pluvio_out')
# estpluvio=al.get_tables(ConfigFile,'-plu')

# print '\n'
# print 'Se ejecutan figuras comparativas de niveles simulados'
# print '\n'

# # NOTA: La ejecucion de esta funcion se debe descomentar cuando se tenga QHist de almenos una hora. Antes saca error.
# # al.Graph_Levels(ruta_inQhist,ruta_inQsim,ruta_outLevelspng,ruta_out_rain,dateText,nodosim,codeest,mediah,ruta_outNsim,res_estadistico,pluvio_out,res_pluvioforecast,estpluvio)

# # #Ruta donde se borraran graficas viejas
# # ruta_erase_png = al.get_ruta(ConfigFile, 'ruta_levelspng')
# # #Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
# # al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=False)



# #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

dateText = dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

print '\n'
print '###################################### FIN DEL CRON: '+dateText+' #############################\n'
