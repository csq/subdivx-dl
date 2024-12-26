# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import logging
import argparse
import tempfile

from .version import __version__
from .verchk import run_check_version

# Check for updates
class CheckUpdateAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        run_check_version()
        exit(0)

# Parser for command-line
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Subdvix-dl is a subtitle downloader for the website subdvix.com',
    epilog='''Disclaimer: subdvix.com not involve in this development.\n
            \rAny bug report, questions about this software do it at\n \
            \r<www.github.com/csq/subdivx-dl/issues>'''
)

# Parser main
parser.add_argument('SEARCH', help='name of the TV series or movie to search for subtitles')

# Create a group for startup-related arguments
startup_group = parser.add_argument_group('Startup')
startup_group.add_argument('-V', '--version', action='version', version=__version__)
startup_group.add_argument('-v', '--verbose', help='enable verbose output', action='store_true')
startup_group.add_argument('-cu', '--check-update', help='check availability of updates', action=CheckUpdateAction, nargs=0)

# Create a group for download-related arguments
download_group = parser.add_argument_group('Download')
download_group.add_argument('-s', '--season', help='download subtitles for the entire season', action='store_true')
download_group.add_argument('-l', '--location', help='specify the destination directory')
download_group.add_argument('-nr', '--no-rename', help='disable file renaming', action='store_true')
download_group.add_argument('-f', '--fast', help='directly download the best matching subtitle', action='store_true')

# Create a group for results-related arguments
results_group = parser.add_argument_group('Results')
results_group.add_argument('-odates', '--order-by-dates', help='order results by dates', action='store_true')
results_group.add_argument('-odownloads', '--order-by-downloads', help='order results by number of downloads', action='store_true')
results_group.add_argument('-n', '--lines', help='limit the number of results', type=int)
results_group.add_argument('-c', '--comments', help='display comments', action='store_true')

# Create a group for style-related arguments
style_group = parser.add_argument_group('Style')
style_group.add_argument('-m', '--minimal', help='use a minimal style for results', action='store_true')
style_group.add_argument(
    '-st', '--style',
    help='show results in the selected style',
    choices=[
        'simple', 'grid', 'pipe', 'presto', 'orgtbl', 'psql',
        'rst', 'simple_grid', 'rounded_grid', 'fancy_grid',
        'heavy_grid', 'double_grid', 'mixed_grid'
    ],
    nargs='?',
    const='rounded_grid'
)

# Create a group for configuration-related arguments
config_group = parser.add_argument_group('Configuration')
config_group.add_argument('-sc', '--save-config', help='save configuration', action='store_true')
config_group.add_argument('-lc', '--load-config', help='load configuration', action='store_true')

# Create and configure logger
logger = logging.getLogger(__name__)

fullfmt = '[%(asctime)s] |%(levelname)s| %(message)s'
compactfmt = '|%(levelname)s| %(message)s'

datefmt = '%d/%m/%y %H:%M:%S'

# Get the temporary directory
temp_dir = tempfile.gettempdir()

# Choose appropriate file path based on the platform
log_file = os.path.join(temp_dir, 'subdivx-dl.log')

args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.INFO, format=compactfmt)
else:
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        encoding='utf-8',
        level=logging.INFO,
        format=fullfmt,
        datefmt=datefmt
    )
