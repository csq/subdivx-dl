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

def main():

	PAGE_NUM = 1
	titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE, PAGE_NUM)
	
	while (1):
		# Clear screen
		clear()

		# Show Search Results
		printSearchResult(args, titleList, downloadList, dateList, userList)

		if len(titleList) == 100 and PAGE_NUM == 1:
			print('\n[ n ] Next page')
		elif len(titleList) == 100 and PAGE_NUM > 1:
			print('\n[n/p] Next/Previous page')
		elif len(titleList) < 100 and PAGE_NUM > 1:
			print('\n[ p ] Previous page')
		print('\n[1~9] Select')
		print('[ 0 ] Exit\n')

		inputUser = input('Selection: ')

		try:
			selection = int(inputUser)-1
			url = urlList[selection]
		except ValueError:
			if len(titleList) == 100 and PAGE_NUM > 1:
				if inputUser == 'n':
					PAGE_NUM = PAGE_NUM + 1
					titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE, PAGE_NUM)
					continue
				elif inputUser == 'p':
					PAGE_NUM = PAGE_NUM - 1
					titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE, PAGE_NUM)
					continue
			elif len(titleList) < 100 and PAGE_NUM > 1:
				if inputUser == 'p':
					PAGE_NUM = PAGE_NUM - 1
					titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE, PAGE_NUM)
					continue
			elif len(titleList) == 100 and PAGE_NUM == 1:
				if inputUser == 'n':
					PAGE_NUM = PAGE_NUM + 1
					titleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE, PAGE_NUM)
					continue
			else:
				print('\nInput valid options')
				time.sleep(1)
				continue
			print('\nInput valid options')
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
		printSelectDescription(args, selection, descriptionList)

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