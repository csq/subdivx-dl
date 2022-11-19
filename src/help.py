import argparse

parser = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Subdvix-dl is a subtitle downloader of website subdvix.com',
    epilog='''Disclaimer: subdvix.com not involve in this development.\n
           \rAny comments about this software make it in:\n \
	       \r<www.github.com/csq/subdivx-dl> or <www.gitlab.com/csq1/subdivx-dl>'''
)

parser.add_argument('SEARCH', help='Name at serie or movie to search subtitle')
parser.add_argument('-v','--version', action='version', version='2022.07.31')
parser.add_argument('-s', '--season', help='download full season subtitles', action='store_true')