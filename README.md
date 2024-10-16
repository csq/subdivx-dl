# Subdivx-dl
CLI tool for search and download subtitles for the site www.subdivx.com

## Other language
- [Español](README-es.md)  

## INSTALLATION
You can install subdivx-dl by following these steps:

Download the repository

    git clone www.github.com/csq/subdivx-dl

Enter into the folder ``subdivx-dl`` and execute

    pip install .

### DEPENDENCIES
Python versions 3.6+ are supported. Other versions and implementations may or may not work correctly.

Libraries:
* Tabulate
* Urllib3
* Rarfile
* Guessit

## FIRST USE
Configure cookies and token, take this data from Developer Tools of your browser.

Example in Firefox
Open Developer Tools (**Ctrl+Shift+I**)

Copy ``cf_clearance`` and ``sdx`` values

<img src="img/img-06.png" width="800" height="400"/>

&nbsp;

Copy ``token`` value

<img src="img/img-07.png" width="800" height="400"/>

&nbsp;

Paste all values

![example](img/img-08.png)

## USAGE AND OPTIONS
    subdivx-dl [OPTIONS][SEARCH]

### Opciones Generales:
    -h, --help                          Print this help text and exit
    -V, --version                       Print program version and exit
    -s, --season                        Download full season subtitles
    -l, --location LOCATION             Download subtitle in destination directory
    -n, --lines LINES                   Limit the number of results
    -g, --grid                          Print results in a grid format
    -nr, --no-rename                    Disable rename files
    -c, --comments                      Show subtitles comments in search
    -f, --first                         Download the first matching
    -odownloads, --order-by-downloads   Order results by downloads
    -odates, --order-by-dates           Order results by dates
    -v, --verbose                       Be verbose

#### Examples
These examples show habitual operation

Search and download a single subtitle in the current directory

    subdivx-dl 'Silicon Valley S01E01'  

    or  
    
    subdivx-dl 'The.Matrix.Revolutions.2003.REMASTERED.1080p.10bit.BluRay.8CH.x265.HEVC-PSA.mkv'  

Search and download multiples subtitles in same directory

    subdivx-dl -s 'Silicon Valley S01'

Search and download a subtitle in specific directory (directory is create if it does not exist)

    subdivx-dl -l ~/Downloads/MyDirectory/ 'Silicon Valley S01E01'

Search and download a subtitle but not renaming file (keep name of origin)

    subdivx-dl -nr 'Matrix'

Search subtitle including their comments

    subdivx-dl -c 'Halo S01E01'

Download subtitle directly

    subdivx-dl -f 'It Crowd S02E01'

### Screenshots
Search results view  
![example](img/img-01.png)

Description view  
![example](img/img-02.png)

Selection view: in case of having multiple subtitles  
![example](img/img-03.png)

Search results view in a grid format  
![example](img/img-04.png)

Description view with comments in a grid format  
![example](img/img-05.png)


## Troubleshooting
**Subtitles not found**  

**Note**: If a cookie is not found during the initial search, you will receive the message 'Subtitles not found'. Retry the search to normalize the process.

If the message 'Subtitles not found' is ever returned, follow these steps:
* Delete the cookie file named **sdx-dl** in the temporary folder
    * Windows: ``C:\Users\user_name\AppData\Local\Temp``  
    * Linux: ``/tmp``  
* Perform the search again


**Uncompress rar files**  

The module ``rarfile`` specifies:
>Compressed files are extracted by executing external tool: unrar (preferred), unar, 7zip or bsdtar.

Therefore, you must have one of these tools installed.

### Author
subdivx-dl was created by [Carlos Quiroz](https://github.com/csq/)

### Disclaimer
subdvix.com does not participate in this development.

### License
GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.