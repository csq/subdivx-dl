# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
from .utils import *

SUBDIVX_URL = 'https://www.subdivx.com/inc/ajax.php'

args = helper.parser.parse_args()
FIND_SUBTITLE = args.SEARCH

user_agent = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0'}
http = urllib3.PoolManager(headers=user_agent)

def main():

	PAGE_NUM = 1
	titleList, descriptionList, idList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE)
	
	while (1):
		# Clear screen
		clear()

		# Show Search Results
		printSearchResult(args, titleList, downloadList, dateList, userList)

		mainMenu()
		inputUser = input('Selection: ')

		try:
			selection = int(inputUser)-1
			id_subtitle = str(idList[selection])
			url = 'https://subdivx.com/'+id_subtitle
		except ValueError:
			if len(titleList) == 100:
				titleList, descriptionList, idList, downloadList, userList, dateList = getDataPage(args, http, SUBDIVX_URL, FIND_SUBTITLE)
				continue
			else:
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

		# Checking flag for add comments view
		if (args.comments == True):
			commentList = getComments(http, SUBDIVX_URL, id_subtitle)
			if not commentList:
				pass
			else:
				printSelectComments(args, commentList)

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
			getSubtitle(user_agent, args, url)
			exit(0)
		elif select_action == 0:
			clear()
			exit(0)

if __name__ == '__main__':
	main()