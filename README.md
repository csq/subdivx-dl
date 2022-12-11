# Subdivx-dl

CLI tool for download subtitle for the site www.subdivx.com

## INSTALLATION

You can install subdivx-dl using for the moment this a workaround:  

  Change permission

    sudo chmod +x /{directory}/subdivx-dl/subdivx-dl

Add path to .bashrc or .zshrc

    export PATH=$PATH:/{directory}/subdivx-dl/subdivx-dl


### DEPENDENCIES
Python versions 3.0+ are supported. Other versions and implementations may or may not work correctly.  

Libraries:
* BeautifulSoup
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
    -nr, --no-rename                Disable rename files

    --order-by-downloads            Print order results by downloads
    --order-by-dates                Print order results by dates

#### Examples
These examples show habitual operation

Download single subtitle in actual directory

    subdivx-dl 'Silicon Valley S01E01'

Download multiples subtitles in same directory

    subdivx-dl 'Silicon Valley S01' -s

Search and order by most downloaded

    subdivx-dl 'Silicon Valley S01E01' --order-by-downloads

Download subtitle in specific directory

    subdivx-dl 'Silicon Valley S01E01' -l ~/Downloads/MyDirectory/

Download subtitle but not renaming file (keep name of origin)

    subdivx-dl 'Matrix' -nr

### Screenshots
Search results view
![example](img/img-01.png)

Description view
![example](img/img-02.png)

Selection view: in case of multiple subtitles
![example](img/img-03.png)

### Disclaimer
subdvix.com does not participate in this development.
