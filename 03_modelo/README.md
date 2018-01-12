# 03_modelo

Esta carpeta contiene el respaldo de la ejecución operacional del modelo hidrológico y la generación de resultados.
Cada carpeta contenida corresponde a cada cuenca simulada, cada una contiene:

- setting (carpeta): todos los archivos de texto con las rutas y la configuración necesaria para setear cada ejecución del modelo.

- cron.py (archivo): codigo a ser croneado para la ejecución, desde este se invoca todas las funciones para la ejecución del modelo 
y el despliegue de resultados.

- log.text (archivo): archivos de texto con el log del cron.

- resultados (carpeta): todos los archivos de resultado (msg, json, etc), con la información a desplegar.

- backsto (carpeta): los binario de almacenamiento de cada tanque para realizar updates de acuerdo a los dispuesto en el configfile.
