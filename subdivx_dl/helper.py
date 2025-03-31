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

# Check positive number
def positive_number(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{value} must be a numeric value')
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f'{value} should be greater than zero')
    return ivalue

# Parser for command-line
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    usage='subdivx-dl [OPTIONS] [SEARCH]',
    description='Subdivx-dl is a subtitle downloader for subdivx.com',
    epilog='''Disclaimer: subdivx.com is not involved in this development.\n
            \rReport bugs or ask questions at <www.github.com/csq/subdivx-dl/issues>'''
)

# Parser main
parser.add_argument('SEARCH', help='name of the TV series or movie to search for subtitles')

# Create a group for startup-related arguments
startup_group = parser.add_argument_group('Startup').add_mutually_exclusive_group()
startup_group.add_argument('-V', '--version', action='version', version=__version__)
startup_group.add_argument('-v', '--verbose', help='enable verbose output', action='store_true')
startup_group.add_argument('-cu', '--check-update', help='check availability of updates', action=CheckUpdateAction, nargs=0)
startup_group.add_argument('-dh', '--disable-help', help='disable help messages', action='store_true')

# Create a group for download-related arguments
download_group = parser.add_argument_group('Download')
download_group.add_argument('-s', '--season', help='download subtitles for the entire season', action='store_true')
download_group.add_argument('-l', '--location', help='specify the destination directory')
download_group.add_argument('-nr', '--no-rename', help='disable file renaming', action='store_true')
download_group.add_argument('-ne', '--no-exit', help='disable automatic exit', action='store_true')
download_group.add_argument('-f', '--fast', help='directly download the best matching subtitle', action='store_true')

# Create a group for ordering-related arguments
order_group = parser.add_argument_group('Order-by').add_mutually_exclusive_group()
order_group.add_argument('-odates', '--order-by-dates', help='order results by dates', action='store_true')
order_group.add_argument('-odownloads', '--order-by-downloads', help='order results by number of downloads', action='store_true')

# Create a group for results-related arguments
results_group = parser.add_argument_group('Results')
results_group.add_argument('-n', '--lines', help='limit the number of results', type=positive_number)
results_group.add_argument('-c', '--comments', help='display comments', action='store_true')

# Create a group form layout-related arguments
layout_group = parser.add_argument_group('Layout').add_mutually_exclusive_group()
layout_group.add_argument('-m', '--minimal', help='use a minimal layout for results', action='store_true')
layout_group.add_argument('-a', '--alternative', help='use an alternative layout for results', action='store_true')
layout_group.add_argument('-cmp', '--compact', help='use an compact layout for results', action='store_true')

# Create a group for style-related arguments
style_group = parser.add_argument_group('Style')
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
config_group = parser.add_argument_group('Configuration').add_mutually_exclusive_group()
config_group.add_argument('-sc', '--save-config', help='save configuration', action='store_true')
config_group.add_argument('-lc', '--load-config', help='load configuration', action='store_true')

# Create and configure logger
logger = logging.getLogger(__name__)

def configure_logger(level: str, format_str: str, save_to_file: bool) -> None:
    log_name = 'subdivx-dl.log'

    kwargs = {
        "level": getattr(logging, level.upper()),
        "format": format_str,
        "datefmt": "%d/%m/%y %H:%M:%S",
    }
    if save_to_file:
        kwargs["filename"] = os.path.join(tempfile.gettempdir(), log_name)
        kwargs["filemode"] = "w"
        kwargs["encoding"] = "utf-8"
    logging.basicConfig(**kwargs)

# Format string
fullfmt = '[%(asctime)s] |%(levelname)s| %(message)s'
compactfmt = '|%(levelname)s| %(message)s'

args = parser.parse_args()

if args.verbose:
    configure_logger(level='info', format_str=compactfmt, save_to_file=False)
else:
    configure_logger(level='info', format_str=fullfmt, save_to_file=True)
