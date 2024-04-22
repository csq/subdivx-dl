# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import logging
import tempfile
import os

# Parser for command-line
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Subdvix-dl is a subtitle downloader for the website subdvix.com',
    epilog='''Disclaimer: subdvix.com not involve in this development.\n
            \rAny bug report, questions about this software do it at\n \
            \r<www.github.com/csq/subdivx-dl/issues>'''
)

parser.add_argument('SEARCH', help='name of the tv serie or movie to search for subtitle')
parser.add_argument('-V', '--version', action='version', version='2024.03.20')
parser.add_argument('-s', '--season', help='download full season subtitles', action='store_true')
parser.add_argument('-l', '--location', help='destination directory')
parser.add_argument('-g', '--grid', help='show results in a grid', action='store_true')
parser.add_argument('-nr', '--no-rename', help='disable rename files', action='store_true')
parser.add_argument('-c', '--comments', help='show comments', action='store_true')
parser.add_argument('-f', '--first', help='download the first matching', action='store_true')
parser.add_argument('-v', '--verbose', help='be verbose', action='store_true')

# Create and configure logger
logger = logging.getLogger(__name__)

fmt_full = '[%(asctime)s] |%(levelname)s| %(message)s'
fmt_compact = '|%(levelname)s| %(message)s'

datefmt = '%d/%m/%y %H:%M:%S'

# Get the temporary directory
temp_dir = tempfile.gettempdir()

# Choose appropriate file path based on the platform
log_file = os.path.join(temp_dir, 'subdivx-dl.log')

args = parser.parse_args()

if (args.verbose):
    logging.basicConfig(level=logging.INFO, format=fmt_compact)
else:
    logging.basicConfig(filename=log_file, filemode='w', encoding='utf-8', level=logging.DEBUG, format=fmt_full, datefmt=datefmt)