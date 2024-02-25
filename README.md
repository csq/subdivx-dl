# Subdivx-dl
CLI tool for search and download subtitles for the site www.subdivx.com

## INSTALLATION
You can install subdivx-dl using pip command:

Download the repository

    git clone www.github.com/csq/subdivx-dl

Enter into the folder and execute

    pip install .

### DEPENDENCIES
Python versions 3.0+ are supported. Other versions and implementations may or may not work correctly.

Libraries:
* Tabulate
* Urllib3

### External dependencies
* [**wget**](https://www.gnu.org/software/wget/) - Required for download archives from the web.
* [**unrar**](https://packages.debian.org/bullseye/unrar) - Required for extract files from rar archives.

**Note**: This external dependency must be present since they are executed by subprocess.

## USAGE AND OPTIONS

    subdivx-dl [SEARCH][OPTIONS]

### General Options:
    -h, --help                      Print this help text and exit
    -v, --version                   Print program version and exit
    -s, --season                    Download full season subtitles
    -l, --location LOCATION         Download subtitle in destination directory
    -g, --grid                      Print results in a grid format
    -nr, --no-rename                Disable rename files
    -c, --comments                  Show subtitles comments in search

#### Examples
These examples show habitual operation

Search single subtitle in actual directory

    subdivx-dl 'Silicon Valley S01E01'

Search multiples subtitles in same directory

    subdivx-dl 'Silicon Valley S01' -s

Search subtitle in specific directory (directory is create if it does not exist)

    subdivx-dl 'Silicon Valley S01E01' -l ~/Downloads/MyDirectory/

Search subtitle but not renaming file (keep name of origin)

    subdivx-dl 'Matrix' -nr

Search subtitle including comments

    subdivx-dl 'Halo S01E01' -c

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

### Author
subdivx-dl was created by [Carlos Quiroz](https://github.com/csq/)

### Disclaimer
subdvix.com does not participate in this development.

### License
GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.