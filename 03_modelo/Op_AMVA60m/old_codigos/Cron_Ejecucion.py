
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
# import json

# Texto Fecha: el texto de fecha que se usa para guardar algunos archivos de figuras.
date = dt.datetime.now()
dateText = dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

print '\n'
print '###################################### Fecha de Ejecucion: '+dateText+' #############################\n'

#Obtiene las rutas necesarias 
ruta_de_rutas = '/media/nicolas/Home/Jupyter/Soraya/Op_Alarmas/Op_AMVA60m/Rutas.md'
RutasList = al.get_rutesList(ruta_de_rutas)

# rutas de objetos de entrada
ruta_cuenca = al.get_ruta(RutasList, 'ruta_cuenca')
ruta_campos = al.get_ruta(RutasList, 'ruta_campos')
ruta_codigos = al.get_ruta(RutasList, 'ruta_codigos')
ruta_configuracion_1 = al.get_ruta(RutasList, 'ruta_configuracion_1')
ruta_almacenamiento = al.get_ruta(RutasList, 'ruta_almacenamiento')
# Rutas de objetos de salida
ruta_out_rain = al.get_ruta(RutasList, 'ruta_rain')
ruta_out_rain_png = al.get_ruta(RutasList, 'ruta_rain_png')


#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

print '###################################### CONSULTA DE LA LLUVIA Y EXTRAPOLACION ############################\n'

#-------------------------------------------------------------------
#GENERA EL CAMPO DE LLUVIA DE LOS ULTIMOS 15MIN Y LOS PROXIMOS 60
#-------------------------------------------------------------------
# Obtiene el datetime 
fecha_1 =  date + dt.timedelta(hours = 5) - dt.timedelta(minutes = 10)
fecha_2 =  date + dt.timedelta(hours = 5) + dt.timedelta(minutes = 60) 
# Lo convierte en texto 
fecha1 = fecha_1.strftime('%Y-%m-%d')
fecha2 = fecha_2.strftime('%Y-%m-%d')
hora_1 = fecha_1.strftime('%H:%M')
hora_2 = fecha_2.strftime('%H:%M')
# Ejecuta para obtener el campo de lluvia en la proxima hora 
lluvia_actual = ruta_out_rain + 'Lluvia_actual'
comando = ruta_codigos+'Rain_Rain2Basin.py '+fecha1+' '+fecha2+' '+ruta_cuenca+' '+ruta_campos+' '+lluvia_actual+' -t 300 -j -u 0.0005 -1 '+hora_1+' -2 '+hora_2
os.system(comando)
# Imprime mensaje de exito
print 'Aviso: Lluvia actual + extrapolacion generados en: '
print lluvia_actual+'\n'

#-------------------------------------------------------------------
#ACTUALIZA EL CAMPO DE LLUVIA HISTORICO DE LA CUENCA 
#-------------------------------------------------------------------
#Luvia historica 
lluvia_historica = ruta_out_rain + 'Lluvia_historica'
#Fechas de inicio y fin 
fecha_1 =  date + dt.timedelta(hours = 5) - dt.timedelta(minutes = 5)
fecha_2 =  date + dt.timedelta(hours = 5) + dt.timedelta(minutes = 0)
# Lo convierte en texto 
fecha1 = fecha_1.strftime('%Y-%m-%d')
fecha2 = fecha_2.strftime('%Y-%m-%d')
hora_1 = fecha_1.strftime('%H:%M')
hora_2 = fecha_2.strftime('%H:%M')
# Ejecuta para actualizar el campo de lluvia 
comando = ruta_codigos+'Rain_Rain2Basin.py '+fecha1+' '+fecha2+' '+ruta_cuenca+' '+ruta_campos+' '+lluvia_historica+' -t 300 -j -u 0.0005 -o True -n -1 '+hora_1+' -2 '+hora_2
os.system(comando)
#imprime aviso 
print 'Aviso: Lluvia historica actualizada en: '
print lluvia_historica+'\n'

#-------------------------------------------------------------------
#GENERA GRAFICAS DE CAMPOS
#-------------------------------------------------------------------
fecha2 = date.strftime('%Y-%m-%d-%H:%M')

print 'Aviso: Se generan graficas de radar para los intervalos:'

# Grafica de la lluvia en los ultimos 3 dias 
fecha1 = date - dt.timedelta(hours = 72)
fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
ruta_figura = ruta_out_rain_png + 'Acumulado_3dias.png'
r3dias=al.Graph_AcumRain(fecha1,fecha2,ruta_cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=80)

# Grafica de la lluvia en los ultimas 24 horas
fecha1 = date - dt.timedelta(hours = 24)
fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
ruta_figura = ruta_out_rain_png + 'Acumulado_1dia.png'
r1dia=al.Graph_AcumRain(fecha1,fecha2,ruta_cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=80)

# Grafica en la ultima hora.
fecha1 = date - dt.timedelta(hours = 1)
fecha1 = fecha1.strftime('%Y-%m-%d-%H:%M')
ruta_figura = ruta_out_rain_png + 'Acumulado_1hora.png'
r1hr=al.Graph_AcumRain(fecha1,fecha2,ruta_cuenca,lluvia_historica,ruta_figura,vmin=0,vmax=10)

#Grafica en los proximos 30min
fecha1 = fecha2
fecha2= date + dt.timedelta(minutes = 30)
fecha2 = fecha2.strftime('%Y-%m-%d-%H:%M')
ruta_figura = ruta_out_rain_png + 'Acumulado_30siguientes.png'
r30minnext=al.Graph_AcumRain(fecha1,fecha2,ruta_cuenca,lluvia_actual,ruta_figura,vmin=0,vmax=20)


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

print '###################################### EJECUCION DEL MODELO ############################\n'

#Explicacion: Se pueden configurar diferentes ejecuciones con diferentes productos 
#	de lluvia, este caso es uno de ejemplo.

#Ejecucion del modelo en el ultimo intervalo de tiempo
comando = ruta_codigos+'Model_Ejec.py '+ruta_cuenca+' '+ruta_configuracion_1+' -v'
os.system(comando)
time.sleep(15)

#Actualiza las condiciones del modelo 
comando = ruta_codigos+'Model_Update_Store.py '+dateText+' '+ruta_configuracion_1+' -v'
os.system(comando)

# #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# #||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
print '\n'
print '###################################### PRODUCCION DE FIGURAS Y RESULTADOS ############################\n'

# Para esta cuenca se ejecutan figuras siempre para mostrar los resultados en la pagina de SIATA

#Lectura del archivo de configuracion
ConfigFile = al.get_rutesList(ruta_configuracion_1)

# #Actualiza json con los caudaes simulados de la parametrizacion escogida para mostrar en la pagina

#Se define ruta sin extension del Qhist de la parametrizacion a incluir
ruta_qhistJson = al.get_ruta(ConfigFile,'ruta_qhist2Json')
#Se define ruta sin extension del Qsim de la parametrizacion a incluir
ruta_qsimJson = al.get_ruta(ConfigFile,'ruta_qsim2Json')
#Se define la ruta donde se escribe el Json.
ruta_outJson = al.get_ruta(ConfigFile,'ruta_Json')
#JSON
al.Genera_json(ruta_qhistJson,ruta_qsimJson,ruta_outJson)

#Figura de la evolucion de los caudales en el cauce

ListaEjec = []
for i in range(13):
    fechaNueva = date + dt.timedelta(minutes = 5*i)
    fechaNueva = fechaNueva.strftime('%Y-%m-%d-%H:%M')
    comando = ruta_codigos+'Graph_StreamFlow_map.py '+fechaNueva+' '+ruta_cuenca+' '+ruta_configuracion_1+' -r '+str(i+1)
    ListaEjec.append(comando)
#Ejecuta lass figuras en paralelo 
p = Pool(processes = 10)
p.map(os.system, ListaEjec)
p.close()
p.join()

print '\n'
print 'Se ejecutan figuras con mapa de StreamFlow'
print '\n'

#Ruta donde se borraran graficas viejas
ruta_erase_png = al.get_ruta(ConfigFile, 'ruta_map_qsim')
#Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen 
al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)

#Figura de la humedad simulada en el tiempo actual

#lista de ejecuciones
ListaEjec = []
fechaNueva = date 
fechaNueva = fechaNueva.strftime('%Y-%m-%d-%H:%M')
comando = ruta_codigos+'Graph_Moisture_map.py '+dateText+' '+ruta_cuenca+' '+ruta_configuracion_1
ListaEjec.append(comando)
#Ejecuta las figuras en paralelo 
p = Pool(processes = 3)
p.map(os.system, ListaEjec)
p.close()
p.join()

print '\n'
print 'Se ejecutan figuras con mapa de Humedad'
print '\n'

#Ruta donde se borraran graficas viejas
ruta_erase_png = al.get_ruta(ConfigFile, 'ruta_map_humedad')
#Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)


#Figura de los deslizamiento simuados en el tiempo acumulado - 5 min.

ListaEjec = []
fechaNueva = date
fechaNueva = fechaNueva.strftime('%Y-%m-%d-%H:%M')
comando = ruta_codigos+'Graph_Slides_map.py '+dateText+' '+ruta_cuenca+' '+ruta_configuracion_1
ListaEjec.append(comando)
#Ejecuta las figuras en paralelo 
p = Pool(processes = 3)
p.map(os.system, ListaEjec)
p.close()
p.join()
print '\n'
print 'Se ejecutan figuras con mapa de Deslizamientos'
print '\n'

#Ruta donde se borraran graficas viejas
ruta_erase_png = al.get_ruta(ConfigFile, 'ruta_map_slides')
#Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=True)


# #Figura comparativa de niveles simulados vs. observado y los de alerta.
# #Se define ruta de donde se leeran los resultados a plotear
# ruta_inQhist = al.get_ruta(ConfigFile,'ruta_qsim_hist')
# ruta_inQsim = al.get_ruta(ConfigFile,'ruta_qsim')
# #se leen cosas necesarias para la funcion
# nodosim = al.get_ruta(ConfigFile,'nodosim')
# codeest = al.get_ruta(ConfigFile,'codeestN')
# mediah = al.get_ruta(ConfigFile,'mediaN')
# #Lectura de rutas de salida de la imagen
# ruta_outLevelspng = al.get_ruta(ConfigFile,'ruta_levelspng')
# #Lectura de rutas donde guardar Nsim.
# ruta_outNsim = al.get_ruta(ConfigFile,'ruta_niveles')

# print '\n'
# print 'Se ejecutan figuras comparativas de niveles simulados'
# print '\n'

# al.Graph_Levels(ruta_inQhist,ruta_inQsim,ruta_outLevelspng,ruta_out_rain,dateText,nodosim,codeest,mediah,ruta_outNsim)

# #Ruta donde se borraran graficas viejas
# ruta_erase_png = al.get_ruta(ConfigFile, 'ruta_levelspng')
# #Se borran graficas viejas, se crea animacion y si se asigna se crea o sobreescribe imagen pagina
# al.GraphAnimationsAndDelLast(ruta_erase_png,imagenpagina=False)



#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
#||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

dateText = dt.datetime.now().strftime('%Y-%m-%d-%H:%M')

print '\n'
print '###################################### FIN DEL CRON: '+dateText+' #############################\n'
