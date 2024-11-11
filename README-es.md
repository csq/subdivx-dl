# Subdivx-dl
Herramienta de línea de comandos para buscar y descargar subtítulos del sitio www.subdivx.com

## Otro idioma
- [English](README.md) 

## INSTALACIÓN
Puedes instalar subdivx-dl siguiendo estos pasos:

Descarga el repositorio

    git clone www.github.com/csq/subdivx-dl

Ingresa en la carpeta ``subdivx-dl`` y ejecuta

    pip install .

### DEPENDENCIAS
Python 3.6+ son compatibles. Otras versiones e implementaciones pueden funcionar correctamente o no.

Librerias:
* Tabulate
* Urllib3
* Rarfile
* Guessit

## USO Y OPCIONES
    subdivx-dl [OPTIONS][SEARCH]

### Opciones Generales:
    -h, --help                          Print this help text and exit
    -V, --version                       Print program version and exit
    -s, --season                        Download full season subtitles
    -l, --location LOCATION             Download subtitle in destination directory
    -n, --lines LINES                   Limit the number of results
    -st --style STYLE                   Show results in selected style
    -nr, --no-rename                    Disable rename files
    -c, --comments                      Show subtitles comments in search
    -f, --first                         Download the first matching
    -odownloads, --order-by-downloads   Order results by downloads
    -odates, --order-by-dates           Order results by dates
    -v, --verbose                       Be verbose

#### Ejemplos
Estos ejemplos muestran la operación habitual  

Buscar y descargar un solo subtítulo en el directorio actual  

    subdivx-dl 'Silicon Valley S01E01'  

    or  

    subdivx-dl 'The.Matrix.Revolutions.2003.REMASTERED.1080p.10bit.BluRay.8CH.x265.HEVC-PSA.mkv'  

Buscar y descargar múltiples subtítulos en el mismo directorio  

    subdivx-dl -s 'Silicon Valley S01'

Buscar y descargar un subtítulo en un directorio específico (el directorio se crea si no existe)

    subdivx-dl -l ~/Downloads/MyDirectory/ 'Silicon Valley S01E01'

Buscar y descargar un subtítulo pero sin cambiar el nombre del archivo (mantener el nombre de origen)  

    subdivx-dl -nr 'Matrix'

Buscar subtítulo incluyendo los comentarios  

    subdivx-dl -c 'Halo S01E01'

Descargar el subtítulo directamente sin intervención

    subdivx-dl -f 'It Crowd S02E01'

### Capturas de pantalla
Vista de resultados de búsqueda  
![example](img/img-01.png)

Vista de descripción  
![example](img/img-02.png)

Vista de selección: en caso de tener múltiples subtítulos  
![example](img/img-03.png)

Vista de resultados de búsqueda en formato cuadrícula  
![example](img/img-04.png)

Vista de descripción con comentarios en formato cuadrícula  
![example](img/img-05.png)

## Solución de problemas

**Subtitles not found**

Si el mensaje 'Subtitles not found', se muestra constantemente, sigue estos pasos:

* Elimina la cookie llamada **sdx-dl** en la carpeta temporal.  
    * Windows: ``C:\Users\nombre_de_usuario\AppData\Local\Temp``  
    * Linux: ``/tmp``  
* Realiza la búsqueda nuevamente

**Uncompress rar files**

El módulo ``rarfile`` especifica:
>Los archivos comprimidos se extraen ejecutando una herramienta externa: unrar (preferido), unar, 7zip o bsdtar.

Por lo tanto, debes tener una de estas herramientas instaladas.

### Autor
subdivx-dl fue creado por [Carlos Quiroz](https://github.com/csq/)

### Descargo de responsabilidad
subdvix.com no participa en este desarrollo.

### Licencia
Licencia Pública General de GNU v3.0 o posterior  

Consulta [COPYING](COPYING) para ver el texto completo.