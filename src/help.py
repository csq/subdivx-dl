import argparse

parser = argparse.ArgumentParser(
	description='Subdvix-dl is a subtitle downloader of page subdvix.com',
	epilog='subdvix.com not involve in this development, any comment on software do it <www.github.com/csq/subdivx-dl>.'
)

parser.add_argument('SEARCH', help='Name at serie or movie to search subtitle')
parser.add_argument('-v','--version', action='version', version='2022.07.31')

args = parser.parse_args()