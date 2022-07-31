import argparse

parser = argparse.ArgumentParser(
	description='Subdvix-dl is a subtitle downloader of website subdvix.com',
	epilog='Disclaimer: subdvix.com not involve in this development.\
	        Any comments about this software make it in: \
	        <www.github.com/csq/subdivx-dl> or \
	        <www.gitlab.com/csq1/subdivx-dl>'
)

parser.add_argument('SEARCH', help='Name at serie or movie to search subtitle')
parser.add_argument('-v','--version', action='version', version='2022.07.31')

args = parser.parse_args()