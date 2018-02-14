## Rutas iniciales

Estas rutas son basicas para la ejecucion del modelo.
Para garantizar la lectura de las rutas, estas deben escribirse sin comillas y respetando
los espacios, deben tener la sgte. estructura: - **nombreruta**: ruta.

- **ruta_campos**: /media/nicolas/Home/nicolas/101_RadarClass/
	> Ruta en donde se encuentran los campos de preciptacion a aprtir de radar para todo el area de alcance del sensor.
- **ruta_cuenca**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/01_database/NCs/Barbosa_Slides_60m.nc
	> Ruta en donde se encuentra el .nc de la cuenca para la simulación.
- **ruta_bkc_alm**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/backsto/
        > Ruta en donde se encuentran las copias de almacenamiento que pueden remplazar a las operacionales


## Parametros Modelacion

Se indican parametros propios de la simulación, tales como $dt$ y $dx$:

### Param modelación

- **Dt[seg]**: 300
- **Dx[mts]**: 60.0
- **Almacenamiento medio**: True
- **Separar Flujos**: True
- **Retorno**: 1
- **Nodos Eval**: 1087
- **Qsim Name**: Qsim
- **Almacenamiento medio**: True


> Parametros que afectan directamente a la modelación, se encuentra el paso de tiempo, 
	si hay retorno o no, el nodo en el cual se evalua al modelo, y si se hacen ciertos 
	calculos dentro del modelo.

### Param Deslizamientos
> Parametros para determinar si se hace modelación de deslizamientos o no, además se
puede modificar el factor de seguridad mediante el cual se determina la vulnerabilidad
de las celdas.

- **Simular Deslizamientos**: True
- **Factor de Seguridad FS**: 0.5
- **Factor Corrector Zg**: 1.0

> Algunas cosas necesarias para desplegar la informacion registrada en la cuenca:

- Datos estaciones de nivel:

 Los parametros a continuacion deben tener el mismo numero de elementos separados por un espacio, siempre el primer elemento
deber ser el del nodo de salida con el que se calibra.

- **nodosim**: 1
- **codeestN**: 140
- **mediaN**: 229.959960938

- Estaciones pluviométricas dentro de la cuenca:

En el caso de esta cuenca, debemos incluir todas las estaciones. Por tanto se señalan las que estan por fuera de la cuenca para descartarlas,
y se indica la condicion:

## Estaciones Pluvio por nodos de simulacion:

|-plu|Nivel-cuenca|Est_Pluvioadentro|Est_Pluvioafuera|
|:--:|:----------:|:---------------:|:--------------:|
|-plu|140|160,227,194,190,168,165,63,75,4||


- **pluvio_out**: True


## Rutas de salida - resultados:

Rutas donde se alojan los resultados obtenidos por el modelo.

- **ruta_rain**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/01_rain/
	> Ruta en la que se va a generar el binario de lluvia operacional.
- **ruta_qsim**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/02_caudalsim/
	> Ruta donde se generan el dataframe de Qsim con el  resultado del modelo.
- **ruta_almsim**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/03_humedadsim/
	> Ruta en la cual se van a estar actualizando los almacenamientos del modelo.
- **ruta_almhist**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/03_humedadsim/01_humedadsim_hist/
	> Ruta en la cual se van a estar actualizando los almacenamientos del modelo.
- **ruta_rainHistoryFile**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/01_rain/Lluvia_historica.hdr
	> Archivo plano con historico de lluvia, se usa para evaluar reglas de actualizacion.
- **ruta_qsim_hist**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/02_caudalsim/01_caudalsim_hist/
	> Ruta en donde se actualizan los archivos historicos de caudales simulados 
- **ruta_estadistico**: /media/nicolas/Home/Jupyter/Esneider/modelo_crecidas/pronostico_niveles.bin
        > Ruta en la cual se alojan los resultados del modelo estadistico de crecidas.
- **ruta_pluvioforecast**: /media/nicolas/Home/Jupyter/Esneider/Lluvia_operacional/Salidas/
        > Ruta en la cual se alojan los resultados del pronóstico estadístico para toda la red pluviométrica.
- **ruta_slides**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/04_slidessim/Slides_results.bin
	> Ruta donde se guarda el binario con los mapas de posible ocurrencia de deslizamientos.
- **ruta_qsim2Json**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/02_caudalsim/Qsim_001.json
	> Ruta de donde se toma los resultados de caudal actual de la parametrizacion que se va a montar en el .json
- **ruta_qhist2Json**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/03_modelo/Op_AMVA60m/results/02_caudalsim/01_caudalsim_hist/Qsim_001hist.json
	> Ruta de donde se toma los resultados de caudal historicos de la parametrizacion que se va a montar en el .json
___
## Parametrizacion

Cada una se compone de 10 parámetros escalares, los cuales son:

- R[1] : Evaporación.
- R[2] : Infiltración.
- R[3] : Percolación.
- R[4] : Pérdidas.
- R[5] : Vel Superficial.
- R[6] : Vel Sub-superficial.
- R[7] : Vel Subterranea.
- R[8] : Vel Cauces.
- R[9] : Alm capilar maximo.
- R[10] : Alm gravitacional maximo.

|Nombre | id| evp | ks_v | kp_v | Kpp_v | v_sup | v_sub | v_supt | v_cau | Hu | Hg |
|--------:|----:|:---:|:----:|:----:|:-----:|:-----:|:-----:|:------:|:-----:|:--:|:--:|
| -c | 001 |0.001|150|1.0|0.0|0.6|4.0|0.3|0.99|1.0|1.0|

Los valores de calibración varían de acuerdo a la escala temporal y 
espacial de ejecución del modelo.  Cada uno de estos parámetros es 
multiplicado como un escalar por el mapa que componga una variable **X**
del modelo. 
___
## Almacenamiento 
Indica las rutas en donde se hara lectura y guardado de almacenamiento por el modelo. En la
siguiente tabla se presentan los nombres de los almacenamientos de entrada.  En la tabla se indica:

- **id**: del storage
- **Nombre**: del archivo con las condiciones.
- **Update**: este actualiza (True) o no (False) cada tanto, esto con la finalidad de corregir problemas producidos en el largo plazo.
- **Tiempo**: Cada cuanto se actualiza: Combinaciones tipo pandas (ej, 1h, 2.5h, 15min, etc).
- **Condicion**: Si hay alguna condición para que se de la actualización (se listan a continuación):
    - **No Rain Next Xh**: No se registren lluvias en las siguientes **X** horas.
    - **No Rain Last Xh**: No se registren lluvias en las ultimas **X** horas.
    - **No Rain Xh**: Que no se registren lluvias **X** horas alrededor de la fecha actual.
    > Se pueden incluir más definidas por el usuario.
- **Calib actualiza**: Calibracion a partrir de la cual se actualizan los estados del modelo.
- **Back Sto**: Archivo de background a partir del cual se cambian los estados del modelo cada **Tiempo** y con la **Condicion**.

Condiciones iniciales en caso de que no exista un binario establecido
para alguno de los casos presentados en la tabla:

- **Inicial Capilar**:
- **Inicial Escorrentia**:
- **Inicial Subsup**:
- **Inicial Subterraneo**:
- **Inicial Corriente**:


**Tabla**: almacenamientos de ejecuciones. Nota: Los últimos dos elementos de 'Condicion' deben ser el número de horas y el simbolo 'h'.

|id| Nombre                   | Update | Tiempo[h] | Condicion  | Calib Actualiza | Back Sto        | Slides |
|:-:|:------------------------|:-------:|:------:|:----------:|:---------------:|:---------------:|:------:|
| -s 001| storage_001.StObin | True   | 0     | No Rain Last 0 h | 001          | Sto_wet-s01.StoBin | True|

**Tabla**: Fechas de actualizacion de almacenamientos.

|id     | Nombre                 | Ultima Actualizacion |
|:-----:|:-----------------------|:--------------------:|
| -t 001|CuBarbosa_001_001.StObin|2018-01-23-12:40|


___
## Figuras

Dentro de este apartado se indican las rutas donde se guardan las figuras 
de las simulaciones y los mapas producidos por el modelo. Igualmente se 
indican cual de las parametrizaciones es la que se usa para graficar algunas 
de las variables tales como la animacion de caudales y la evolucion de la 
humedad en la cuenca.

- **ruta_rain_png**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/
        > Ruta en la que se va a generar los .png de acumulado de lluvia.
- **ruta_map_qsim**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/StreamMaps
	> ruta donde se guardan los mapas de caudales simulados. 
- **ruta_map_humedad**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/HumedadMaps
	> Ruta donde se guardan los mapas de humedad.
- **ruta_map_riskvector**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/risk_vector.png
- **ruta_map_slides**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/SlidesMaps
	> Ruta donde se guardan los mapas de deslizamientos producidos por la modelación.
- **ruta_levelspng**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/LevelsGraphs
	> Ruta donde se sgeneran las figuras de simulacion de caudales y niveles.
- **ruta_niveles**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/Nsim/
	> Ruta donde se escriben los niveles simulados corregidos para las graficas de los operacionales
- **ruta_Json**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/05_web/modelo_op/OpAMVA60m/
	> Ruta donde se guarda el json con la Qsim de la parametrizacion escogida.

**Tabla**: Variables y parametrizaciones a plotear.

| Variable		  | Variable |
|:---------------:|:--------:|
| -p Qsim_map 		  | 001|
| -p Humedad_map 	  | 001|
| -p Slides 		  | 001|


	
