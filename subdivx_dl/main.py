# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
import certifi

from .utils import *

SUBDIVX_URL = 'https://www.subdivx.com/'

args = helper.parser.parse_args()
FIND_SUBTITLE = args.SEARCH

headers = {
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'
}

# Create a PoolManager instance for HTTPS requests
https = urllib3.PoolManager(
    headers=headers,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

# Set cookie and get token
set_cookie(https, SUBDIVX_URL, headers)
token = get_token(https, SUBDIVX_URL)

# Save or load configuration
if args.save_config:
	save_config(args)
elif args.load_config:
	config = load_config()
	args = Args(args, config)
else:
	args = Args(args)

def main():

	# Get all data from search
	search_data = get_data_page(args, https, SUBDIVX_URL, token, FIND_SUBTITLE)

	# Sorting data if flag is set
	if args.order_by_downloads or args.order_by_dates:
		search_data = sort_data(args, search_data)

	# Limit the number of results displayed based on the user's preference
	search_data = search_data[:args.lines] if args.lines is not None else search_data

	# Checking flag for switch to fast download mode
	if args.first:
		id_subtitle = search_data[0]['id_subtitle']
		get_subtitle(args, https, SUBDIVX_URL, id_subtitle)
		exit(0)

	while True:
		# Clear screen
		clear()

		# Show Search Results
		print_search_results(args, search_data)

		# Get the user selection
		user_input = prompt_user_for_selection()

		try:
			selection = int(user_input) - 1
			id_subtitle = str(search_data[selection]['id_subtitle'])
		except (ValueError, IndexError):
			print('\nInput valid numbers')
			delay(0)
			continue

		if selection < -1:
			print('\nInput only positive numbers')
			delay(0)
			continue
		elif selection == -1:
			clear()
			exit(0)

		clear()
		print_description(args, selection, search_data)

		# Checking flag for add comments view
		if args.comments:
			comment_list = get_comments(https, SUBDIVX_URL, id_subtitle)
			if not comment_list:
				pass
			else:
				print_comments(args, comment_list)

		# Show selection menu
		user_input = prompt_user_to_download()

		try:
			select_action = int(user_input)
		except ValueError:
			print('\nInput only numbers')
			delay(0)
			continue

		if select_action > 1 or select_action <= -1:
			print('\nInput valid numbers')
			delay(0)
			continue
		elif select_action == 1:
			clear()
			get_subtitle(args, https, SUBDIVX_URL, id_subtitle)
			exit(0)
		elif select_action == 0:
			clear()
			exit(0)

if __name__ == '__main__':
	main()
