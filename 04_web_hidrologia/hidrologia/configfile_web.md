# Archivo de configuración.

## Algunos Metadatos de cada sirena.

### Asignacion de estaciones y otros atributos asociadas a cada sirena.

Notas:
- La cuenca La Lopez (sensor nivel 251) esta contenida en La Gallinaza (186), por eso se asocia a la SIRENA BARBOSA sólo la última.
- Los items en esta tabla sin key '-al' ni codigos no tienen sirena y su informacion no se usa para tal tema.

|-al|Codigo|Nombre_Sirena|Nombre_Quebrada|Est_Nivel|Est_Nivel1|Est_PluvioAdentro|Est_PluvioAfuera|Est_MeteoAdentro|Est_MeteoAfuera|Est_N30m|Est_Tto|
|:-:|:----:|:-----------:|:-------------:|:-------:|:---------------:|:--------------:|:--------------:|:-------------:|:------:|:-----:|
|-al|216|SIRENA SANTA RITA SAN ANTONIO DE PRADO|Q. DONA MARIA|90,108|108|3,18,43||197|249|108||
|-al|219|SIRENA BELEN - LAS VIOLETAS|Q. LA PICACHA|173,116|173|29|1,8||249|||
|-al|220|SIRENA AGUAS FRIAS|Q. PICACHA|173,116|116|29|1,8,9||249|||
|-al|221|SIRENA ANDALUCIA CALDAS|Q. LA CORRALA|259|259||33,253||105||||
|-al|222|SIRENA BARBOSA|Q. LA GALLINAZA|251,186|186||234,30||82|||
|-al|223|SIRENA BELLO CAFETAL|Q. LA LOCA|265,135|135||12,14,48,89|||||
|-al|224|SIRENA LA ESTRELLA|RIO MEDELLIN - LA INMACULADA|179,106,124|106|267,61,261,33,253||105||179,106|179|
|-al|226|SIRENA LA RAYA|Q. LA RAYA|246|246|261|61||105|||
|-al|279|SIRENA PIEDRAS BLANCAS|PIEDRAS BLANCAS|239|239|248|70||70|||
|-al|285|SIRENA EL SALADO - JAMUNDI|EL SALADO|272|272||88,31|||||
|-al|280|SIRENA LA ISLA|LA MADERA Y MONTANITA|283,134|134|281,121|89,14,48|||||
|-al|300|SIRENA LA AVELINA|LA GARCIA||||37,74|||||
|-al|301|EL HATO |EL HATO|155|155||37,74|||||
|||NO SIRENA|RIO MEDELLIN - AULA AMBIENTAL|99||160,227,194,190,168,165,234,30,66,127,31,88,47,72,278,32,75,51,37,74,76,70,248,63,4,275,89,154,121,14,48,242,7,241,24,40,274,55,16,42|||||

### Set de simbologias.

- **risk_names**: LevelAction MinorFlood ModerateFlood MajorFlood MajortotheMajor!
- **risk_colors** #008000 #FFA500 #FF4500 #4B0082 #4B0082

## Rutas inputs

- **ruta_KMLs**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/op/kml/
        > Ruta en la que se alojan los KML's de las cuencas de las alarmas.
- **ruta_nivel**: /media/nicolas/maso/Mario/30daysLevel/
        > Ruta en la que se alojan los .csv de consultad de nivel del ultimos mes.
- **ruta_estadistico**: /media/nicolas/Home/Jupyter/Esneider/modelo_crecidas/pronostico_niveles.bin
        > Ruta en la que se alojan los resultados del modelo estadistico de crecidas y transito.
- **ruta_allrisklevels**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/op/datos_base/risklevels_all_op.csv
        > Ruta en la que se alojan los .csv de consulta de los niveles de riesgo de todas las estaciones de nivel hasta 2018-01-31.
- **ruta_pluvioforecast**: /media/nicolas/Home/Jupyter/Esneider/Lluvia_operacional/Salidas/
        > Ruta en la cual se alojan los resultados del pronóstico estadístico para toda la red pluviométrica.
- **rutaN_infoeventos**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/historicos/nivel/eventos/
        > Ruta en la cual se alojan los estadísticos de los eventos en la historia de las estaciones N
- **rutaP_infoeventos**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/historicos/pluvio/eventos/
        > Ruta en la cual se alojan los estadísticos de los eventos en la historia de las estaciones P

## Rutas outputs

- **ruta_JSONinfosirenas**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/01_estaticos/infosirenas.json
        > Ruta en la que se crea el JSON con la info de asignacion de estaciones y kml's por cada sirena.
- **ruta_JSONnivel**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/02_operacionales/nivel.json
        > Ruta en la que se crea el JSON operacional con la info de de nivel.
- **ruta_JSONpluvio**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/02_operacionales/pluvio.json
        > Ruta en la que se crea el JSON operacional con la info de de pluvio.
- **ruta_GeoJSONnivel**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/01_estaticos/Geo_nivel.geojson
        > Ruta en la que se crea el GeoJSON estatico con la info de los puntos de nivel y el JSON asociado a los datos de cada una.
- **ruta_GeoJSONpluvio**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/01_estaticos/Geo_pluvio.geojson
        > Ruta en la que se crea el GeoJSON estatico con la info de los puntos de pluvio y el JSON asociado a los datos de cada una.
- **ruta_KMLnivel**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/02_operacionales/nivel.kml
        > Ruta en la que se crea el KML operacional con la info de de nivel.
- **ruta_KMLpluvio**: /media/nicolas/Home/Jupyter/Soraya/git/Alarmas/04_web_hidrologia/hidrologia/results/02_operacionales/pluvio.kml
        > Ruta en la que se crea el KML operacional con la info de pluvio.
- **rutaFigsNbandas**: /media/nicolas/Home/Jupyter/Soraya/Op_Alarmas/Result_to_web/Figuras_Alarmas/nivel/
        > Ruta en la que se generan las figuras de N vs Eventos para despliegue web.
- **rutaFigsPbandas**: /media/nicolas/Home/Jupyter/Soraya/Op_Alarmas/Result_to_web/Figuras_Alarmas/pluvio/
        > Ruta en la que se generan las figuras de P vs Eventos para despliegue web.
