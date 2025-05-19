<h1 align="center">
  <b>SUBDIVX-DL</b>
</h1>

<p align="center">
  <strong>CLI Tool for Searching and Downloading Subtitles from subdivx.com</strong><br>
</p>

## OVERVIEW
SUBDIVX-DL is a fast command-line interface (CLI) tool for searching and downloading subtitles, optimized to retrieve the best results with minimal external library usage.

## FEATURES
- **Fast Search**: Quickly find subtitles for your favorite movies and shows.
- **Efficient Downloads**: Download subtitles with ease and speed.
- **Automatic File Renaming**: Automatically rename your downloaded subtitles.
- **Customizable Display**: Adjust the layout and style of search results to suit your preferences.
- **Minimal Dependencies**: Built with a focus on reducing bloat by limiting external library usage.

## AVAILABLE LANGUAGES
- [Español](README-es.md)

## INSTALLATION
You can install subdivx-dl by following these steps:

* Download the repository
    ```bash
        git clone www.github.com/csq/subdivx-dl
    ```
* Enter into the folder ``subdivx-dl`` and execute
    ```bash
        pip install .
    ```

## DEPENDENCIES
Python versions 3.10+ are supported. Other versions and implementations may or may not work correctly.

* **Guessit**: Extracts metadata from media filenames.
* **Certifi**: Collection of root certificates for SSL/TLS validation.
* **Urllib3**: HTTP client for making requests and handling responses.
* **Tabulate**: Formats and displays data in tables for better readability.
* **Patool**: Archive file manager that supports various archive formats.

## USAGE AND OPTIONS
```bash
    subdivx-dl [OPTIONS] [SEARCH]
```
### General options:
```
    Options:
        -h, --help                          Print the help text and exit

    Startup:
        -V, --version                       Print program version and exit
        -v, --verbose                       Enable verbose output
        -cu, --check-update                 Check availability of updates
        -dh, --disable-help                 Disable help messages
        -lcode, --language-code CODE        Specify a custom language code

    Download:
        -s, --season                        Download subtitles for the entire season
        -l, --location LOCATION             Specify the destination directory
        -ns, --new-session                  Create a new session
        -ua', --user-agent                  Specify a custom user agent
        -nr, --no-rename                    Disable file renaming
        -ne, --no-exit                      Disable automatic exit
        -f, --fast                          Directly download the best matching subtitle

    Order-by:
        -odates, --order-by-dates           Order results by dates
        -odownloads, --order-by-downloads   Order by number of downloads

    Results:
        -n, --lines LINES                   Limit the number of results
        -c, --comments                      Display comments

    Layout:
        -m, --minimal                       Show results in a minimal layout
        -a, --alternative                   Show results using an alternative layout
        -cmp, --compact                     Show results in a compact layout

    Style:
        -st, --style STYLE                  Show results in the selected style

    Configuration:
        -sc, --save-config                  Save configuration
        -lc, --load-config                  Load configuration
        -dc, --dump-config                  Dump configuration
```

## USAGE EXAMPLES
These examples show habitual operation

Search and download a single subtitle in the current directory
```bash
    subdivx-dl 'Silicon Valley S01E01'
```
```bash
    subdivx-dl 'The.Matrix.Revolutions.2003.REMASTERED.1080p.10bit.BluRay.8CH.x265.HEVC-PSA.mkv'
```
Search and download multiples subtitles in same directory
```bash
    subdivx-dl -s 'Silicon Valley S01'
```
Search and download a subtitle in specific directory (directory is create if it does not exist)
```bash
    subdivx-dl -l ~/Downloads/MyDirectory/ 'Silicon Valley S01E01'
```
Search and download a subtitle but not renaming file (keep name of origin)
```bash
    subdivx-dl -nr 'Matrix'
```
Search subtitle including their comments
```bash
    subdivx-dl -c 'Halo S01E01'
```
Search subtitles using IMDb ID
```bash
    subdivx-dl 'tt0113243'
```
```bash
    subdivx-dl 'https://www.imdb.com/es/title/tt0113243/'
```
Download the best subtitle directly
```bash
    subdivx-dl -f 'It Crowd S02E01'
```

## VISUAL PERSONALIZATION
### Style
It is possible to apply different styles to the tables that display the results using the ``-st`` or ``--style`` options and specifying the desired style name. The available options are: ``simple``, ``grid``, ``pipe``, ``presto``, ``orgtbl``, ``psql``, ``rst``, ``simple_grid``, ``rounded_grid``, ``fancy_grid``, ``heavy_grid``, ``double_grid`` and ``mixed_grid``. If no style is specified, the default ``rounded_grid`` will be used.

<p align="center">
  <img src="img/styles.gif" alt="animated" />
</p>

### Layout Options
- **`-a`, `--alternative`**: Displays results in an alternative format, presenting the title and description side by side.
<p align="center">
  <img src="img/alternative_layout.png" alt="preview alternative layout" />
</p>

- **`-cmp`, `--compact`**: Shows results in individual tables, with the title and description presented in the same table.
<p align="center">
  <img src="img/compact_layout.png" alt="preview compact layout" />
</p>

- **`-m`, `--minimal`**: Presents results in a minimalist format, showcasing the title, downloads, and dates.
<p align="center">
  <img src="img/minimal_layout.png" alt="preview minimal layout" />
</p>

## CONFIGURATION
### Configuration Management
To save frequently used options for the ``subdivx-dl`` command, the following options are implemented:
* ``-sc`` or ``--save-config``: allows you to save the entered arguments.
* ``-lc`` or ``--load-config``: allows you to perform searches with previously saved arguments.

* The data is stored in:
    * Windows: ``C:\Users\user_name\AppData\Local\subdivx-dl\``
    * Linux: ``~/.config/subdivx-dl/``

## TROUBLESHOOTING

### Uncompressing Files

To extract compressed files using the ``Patool`` library, ensure you have the following tools installed:

- **RAR Files**: Install one of the following:
  - **unrar**
  - **unar**
  - **7zip**

- **7z Files**: Install **7zip**.

Having these tools will allow for the extraction of the corresponding file formats.

### Valid IMDb ID returns no results

A valid IMDb ID may not return results due to an external issue with subdivx.com. The solution is to search by file name or keywords.

## CREDITS AND LEGAL
### Author
subdivx-dl was created by [Carlos Quiroz](https://github.com/csq/)

### Disclaimer
subdivx.com is not involved in this development.

### License
GNU General Public License v3.0 or later
See [COPYING](COPYING) to see the full text.