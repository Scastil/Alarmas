# 04_web_hidrologia

Esta carpeta contiene el respaldo de la generación operacional de archivos para el despliegue en el sitio web operacional con la 
información hidrológica.

- setting (carpeta): todos los archivos de texto con la configuración necesaria para ejecutar los crones.

- cron.py (archivo): codigo a ser croneado para la ejecución, desde este se invoca todas las funciones para la generación de JSONs
y el despliegue de resultados.

- log.text (archivo): archivos de texto con el log del cron.

-resultados (carpeta): todos los archivos de resultado (msg, json, etc), con la información a desplegar.

