# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
from .utils import *

SUBDIVX_URL = 'https://www.subdivx.com/inc/ajax.php'

args = helper.parser.parse_args()
FIND_SUBTITLE = args.SEARCH

user_agent = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0'}
https = urllib3.PoolManager(headers=user_agent)

def main():

	# Get all data from search
	titleList, descriptionList, idList, downloadList, userList, dateList = getDataPage(args, https, SUBDIVX_URL, FIND_SUBTITLE)

	# Checking flag for switch to fast download mode
	if (args.first == True):
		url = 'https://subdivx.com/'+str(idList[0])
		getSubtitle(args, user_agent, url)
		exit(0)

	while (True):
		# Clear screen
		clear()

		# Show Search Results
		printSearchResult(args, titleList, downloadList, dateList, userList)

		# Get the user selection
		userInput = mainMenu()

		try:
			selection = int(userInput) - 1
			id_subtitle = str(idList[selection])
			url = 'https://subdivx.com/'+id_subtitle
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
		printSelectDescription(args, selection, descriptionList)

		# Checking flag for add comments view
		if (args.comments == True):
			commentList = getComments(https, SUBDIVX_URL, id_subtitle)
			if (not commentList):
				pass
			else:
				printSelectComments(args, commentList)

		# Show selection menu
		userInput = selectMenu()

		try:
			select_action = int(userInput)
		except ValueError:
			print('\nInput only numbers')
			time.sleep(1)
			continue

		if (select_action > 1) or (select_action <= -1):
			print('\nInput valid numbers')
			time.sleep(1)
			continue
		elif (select_action == 1):
			clear()
			getSubtitle(args, user_agent, url)
			exit(0)
		elif (select_action == 0):
			clear()
			exit(0)

if __name__ == '__main__':
	main()
