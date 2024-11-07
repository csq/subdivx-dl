# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
import certifi

from .utils import *

SUBDIVX_MAIN_URL = 'https://www.subdivx.com/'
SUBDIVX_URL = 'https://www.subdivx.com/inc/ajax.php'

args = helper.parser.parse_args()
FIND_SUBTITLE = args.SEARCH

headers = {
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
}

https = urllib3.PoolManager(headers=headers, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

setCookie(https, SUBDIVX_MAIN_URL, headers)
token = getToken(https, SUBDIVX_MAIN_URL)

def main():

	# Get all data from search
	searchData = getDataPage(args, https, SUBDIVX_URL, token, FIND_SUBTITLE)

	# Sorting data if flag is set
	if (args.order_by_dates == True or args.order_by_downloads == True):
		searchData = sortData(args, searchData)

	# Limit the number of results displayed based on the user's preference
	searchData = searchData[:args.lines] if args.lines is not None else searchData

	# Checking flag for switch to fast download mode
	if (args.first == True):
		firstSubtitleId = searchData[0]['id_subtitle']
		url = f'https://subdivx.com/{firstSubtitleId}'
		getSubtitle(args, https, url)
		exit(0)

	while (True):
		# Clear screen
		clear()

		# Show Search Results
		printSearchResult(args, searchData)

		# Get the user selection
		userInput = mainMenu()

		try:
			selection = int(userInput) - 1
			idSubtitle = str(searchData[selection]['id_subtitle'])
			url = f'https://subdivx.com/{idSubtitle}'
		except ValueError:
			print('\nInput valid options')
			time.sleep(1)
			continue
		except IndexError:
			print('\nInput valid numbers')
			time.sleep(1)
			continue

		if (selection < -1):
			print('\nInput only positive numbers')
			time.sleep(1)
			continue
		elif (selection == -1):
			clear()
			exit(0)

		clear()
		printSelectDescription(args, selection, searchData)

		# Checking flag for add comments view
		if (args.comments == True):
			commentList = getComments(https, SUBDIVX_URL, idSubtitle)
			if (not commentList):
				pass
			else:
				printSelectComments(args, commentList)

		# Show selection menu
		userInput = selectMenu()

		try:
			selectAction = int(userInput)
		except ValueError:
			print('\nInput only numbers')
			time.sleep(1)
			continue

		if (selectAction > 1) or (selectAction <= -1):
			print('\nInput valid numbers')
			time.sleep(1)
			continue
		elif (selectAction == 1):
			clear()
			getSubtitle(args, https, url)
			exit(0)
		elif (selectAction == 0):
			clear()
			exit(0)

if __name__ == '__main__':
	main()
