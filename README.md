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

    subdivx-dl [OPTIONS][SEARCH]

### General Options:
    -h, --help                      Print this help text and exit
    -V, --version                   Print program version and exit
    -s, --season                    Download full season subtitles
    -l, --location LOCATION         Download subtitle in destination directory
    -g, --grid                      Print results in a grid format
    -nr, --no-rename                Disable rename files
    -c, --comments                  Show subtitles comments in search
    -f, --first                     Download the first matching
    -v, --verbose                   Be verbose

#### Examples
These examples show habitual operation

Search and download a single subtitle in the current directory

    subdivx-dl 'Silicon Valley S01E01'

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

### Author
subdivx-dl was created by [Carlos Quiroz](https://github.com/csq/)

### Disclaimer
subdvix.com does not participate in this development.

### License
GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.