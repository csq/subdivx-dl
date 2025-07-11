<h1 align="center">
  <b>SUBDIVX-DL</b>
</h1>

<p align="center">
  <strong>Herramienta CLI para Buscar y Descargar Subtítulos de subdivx.com</strong><br>
</p>

## DESCRIPCIÓN GENERAL
SUBDIVX-DL es una herramienta de interfaz de línea de comandos (CLI) rápida para buscar y descargar subtítulos, optimizada para obtener los mejores resultados con un uso mínimo de bibliotecas externas.

## CARACTERÍSTICAS
- **Búsqueda Rápida**: Encuentra rápidamente subtítulos para tus películas y programas favoritos.
- **Descargas Eficientes**: Descarga subtítulos con facilidad y rapidez.
- **Renombrado Automático de Archivos**: Renombra automáticamente tus subtítulos descargados.
- **Visualización Personalizable**: Ajusta el diseño y estilo de los resultados de búsqueda según tus preferencias.
- **Dependencias Mínimas**: Diseñado para ser ligero, limitando el uso de bibliotecas externas.

## IDIOMAS DISPONIBLES
- [English](README.md)

## INSTALACIÓN
Puedes instalar subdivx-dl siguiendo estos pasos:

* Descarga el repositorio
    ```bash
        git clone www.github.com/csq/subdivx-dl
    ```
* Ingresa en la carpeta ``subdivx-dl`` y ejecuta
    ```bash
        pip install .
    ```

## ARCHIVOS INDEPENDIENTES
Archivo|Descripción
:---|:---
[subdvix-dl](https://github.com/csq/subdivx-dl/releases/latest/download/subdivx-dl_linux)|Binario independiente x64 para Linux (Ubuntu 24.04+)
[subdvix-dl.exe](https://github.com/csq/subdivx-dl/releases/latest/download/subdivx-dl.exe)|Binario x64 independiente para Windows (Win8+)
[subdvix-dl_x86.exe](https://github.com/csq/subdivx-dl/releases/latest/download/subdivx-dl_x86.exe)|Binario x86 (32-bit) independiente para Windows (Win8+)

## DEPENDENCIAS
Python 3.10+ son compatibles. Otras versiones e implementaciones pueden funcionar correctamente o no.

* **Guessit**: Extrae metadatos de los nombres de archivos multimedia.
* **Certifi**: Colección de certificados raíz para la validación de SSL/TLS.
* **Urllib3**: Cliente HTTP para realizar solicitudes y manejar respuestas.
* **Tabulate**: Formatea y muestra datos en tablas para una mejor legibilidad.
* **Patool**: Gestor de archivos comprimidos que admite varios formatos de archivo.

## USO Y OPCIONES
```bash
    subdivx-dl [OPCIONES] [BUSQUEDA]
```
### Opciones Generales:
```
    Opciones:
        -h, --help                          Imprimir el texto de ayuda y salir

    Inicio:
        -V, --version                       Imprimir la versión del programa y salir
        -v, --verbose                       Habilitar salida detallada
        -cu, --check-update                 Comprobar disponibilidad de actualizaciones

    Descargar:
        -s, --season                        Descargar subtítulos para toda la temporada
        -l, --location UBICACIÓN            Especificar el directorio de destino
        -nr, --no-rename                    Deshabilitar el renombrado de archivos
        -f, --fast                          Descargar directamente el mejor subtítulo coincidente

    Ordenar por:
        -odates, --order-by-dates           Ordenar resultados por fechas
        -odownloads, --order-by-downloads   Ordenar por número de descargas

    Resultados:
        -n, --lines LÍNEAS                  Limitar el número de resultados
        -c, --comments                      Mostrar comentarios

    Diseño:
        -m, --minimal                       Mostrar resultados en un diseño minimo
        -a, --alternative                   Mostrar resultados utilizando un diseño alternativo
        -cmp, --compact                     Mostrar resultados en un diseño compacto

    Estilo:
        -st, --style ESTILO                 Mostrar resultados en el estilo seleccionado

    Misceláneos:
        -dh, --disable-help                 Desactivar los mensajes de ayuda
        -ne, --no-exit                      Desactivar salida automática
        -ns, --new-session                  Crea una nueva session
        -ua', --user-agent                  Definir un agente de usuario personalizado
        -lcode, --language-code CODIGO      Especificar lenguaje predeterminado

    Configuración:
        -sc, --save-config                  Guardar configuración
        -lc, --load-config                  Cargar configuración
        -dc, --dump-config                  Visualizar configuración
```

## EJEMPLOS DE USO
Estos ejemplos muestran la operación habitual

Buscar y descargar un solo subtítulo en el directorio actual
```bash
    subdivx-dl 'Silicon Valley S01E01'
```
```bash
    subdivx-dl 'The.Matrix.Revolutions.2003.REMASTERED.1080p.10bit.BluRay.8CH.x265.HEVC-PSA.mkv'
```
Buscar y descargar múltiples subtítulos en el mismo directorio
```bash
    subdivx-dl -s 'Silicon Valley S01'
```
Buscar y descargar un subtítulo en un directorio específico (el directorio se crea si no existe)
```bash
    subdivx-dl -l ~/Downloads/MyDirectory/ 'Silicon Valley S01E01'
```
Buscar y descargar un subtítulo pero sin cambiar el nombre del archivo (mantener el nombre de origen)
```bash
    subdivx-dl -nr 'Matrix'
```
Buscar subtítulo incluyendo los comentarios
```bash
    subdivx-dl -c 'Halo S01E01'
```
Buscar subtítulos usando el ID de IMDb
```bash
    subdivx-dl 'tt0113243'
```
```bash
    subdivx-dl 'https://www.imdb.com/es/title/tt0113243/'
```
Descarga directamente el mejor subtítulo
```bash
    subdivx-dl -f 'It Crowd S02E01'
```

## PERSONALIZACIÓN VISUAL
### Estilos
Es posible aplicar diferentes estilos a las tablas que muestan los resultados utilizando las opciones ``-st`` o ``--style`` y especificando el nombre del estilo deseado. Las opciones disponible son: ``simple``, ``grid``, ``pipe``, ``presto``, ``orgtbl``, ``psql``, ``rst``, ``simple_grid``, ``rounded_grid``, ``fancy_grid``, ``heavy_grid``, ``double_grid`` y ``mixed_grid``. Si no se especifica un estilo, se utilizará el predeterminado ``rounded_grid``.

<p align="center">
  <img src="img/styles.gif" alt="animated" />
</p>

### Opciones de Diseño
- **`-a`, `--alternative`**: Muestra los resultados en un formato alternativo, presentando el título y la descripción uno al lado del otro.
<p align="center">
  <img src="img/alternative_layout.png" alt="vista previa diseño alternative" />
</p>

- **`-cmp`, `--compact`**: Muestra los resultados en tablas individuales, con el título y la descripción presentados en la misma tabla.
<p align="center">
  <img src="img/compact_layout.png" alt="vista previa diseño compact" />
</p>

- **`-m`, `--minimal`**: Presenta los resultados en un formato minimalista, mostrando el título, las descargas y las fechas.
<p align="center">
  <img src="img/minimal_layout.png" alt="vista previa diseño minimal" />
</p>

## IDIOMA
### Cambiar el idioma de visualización
La aplicación detecta automáticamente el idioma según la configuración regional de su sistema operativo. Actualmente, solo se admiten el inglés y el español, con el idioma predeterminado configurado en 'en' si no se puede reconocer el idioma de la configuración regional.

También puede cambiar el idioma manualmente utilizando el siguiente comando:
* `-lcode CÓDIGO` o `--language-code CÓDIGO`: Esta opción le permite especificar el idioma, donde CÓDIGO puede ser 'en' para inglés o 'es' para español.

## CONFIGURACIÓN
### Gestión de la configuración
Para guardar las opciones frecuentemente utilizadas con el comando ``subdivx-dl``, se implementan siguientes opciones:
* ``-sc`` o ``--save-config``: permite guardar los argumentos ingresados.
* ``-lc`` o ``--load-config``: permite realizar búsquedas con argumentos previamente guardados.
* ``-dc`` o ``--dump-config``: imprime la ubicación del archivo de configuración y los ajustes seteados.

## SOLUCIÓN DE PROBLEMAS

### Descompresión de Archivos

Para extraer archivos comprimidos utilizando la biblioteca ``Patool``, asegúrate de tener instaladas las siguientes herramientas:

- **Archivos RAR**: Instala una de las siguientes:
  - **unrar**
  - **unar**
  - **7zip**

- **Archivos 7z**: Instala **7zip**.

Contar con estas herramientas permitirá la extracción de los formatos de archivo correspondientes.

### ID IMDb válido sin resultados

Un ID de IMDb válido puede no devolver resultados debido a un problema externo con subdivx.com. La solución es buscar por nombre de archivo o palabras clave.

# CRÉDITOS Y LEGAL
### Autor
subdivx-dl fue creado por [Carlos Quiroz](https://github.com/csq/)

### Descargo de responsabilidad
subdivx.com no está involucrado en este desarrollo.

### Licencia
Licencia Pública General de GNU v3.0 o posterior
Consulta [COPYING](COPYING) para ver el texto completo.