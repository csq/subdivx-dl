#!/usr/bin/env python3
# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3

from .utils import *

SUBDIVX_URL = "https://www.subdivx.com/"

args = parser.parse_args()
FIND_SUBTITLE = args.SEARCH

user_agent = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0'}
http = urllib3.PoolManager(headers=user_agent)

titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE)

def main():
	while (1):
		# Clear screen
		clear()

		# Show Search Results
		printSearchResult(titleList, downloadList, dateList, userList)

		print('\n[1~9] Select')
		print('[ 0 ] Exit\n')

		try:
			selection = int(input('Selection: '))-1
			url = urlList[selection]
		except ValueError:
			print('\nInput only numbers')
			time.sleep(1)
			continue
		except IndexError:
			print('\nInput valid numbers')
			time.sleep(1)
			continue

		if selection < -1:
			print('\nInput only positive numbers')
			time.sleep(1)
			continue
		elif selection == -1:
			clear()
			exit(0)

		clear()
		printSelectDescription(selection, descriptionList)

		print('\n[ 1 ] Download')
		print('[ 0 ] Exit\n')

		try:
			select_action = int(input('Selection: '))
		except ValueError:
			print('\nInput only numbers')
			time.sleep(1)
			continue

		if select_action == 1:
			clear()
			request = http.request('GET', url)
			getSubtitle(args, request, SUBDIVX_URL)
			exit(0)
		elif select_action == 0:
			clear()
			exit(0)

if __name__ == '__main__':
	main()