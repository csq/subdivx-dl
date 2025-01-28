# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
import certifi

from .utils import *

SUBDIVX_URL = 'https://www.subdivx.com/'

args = helper.parser.parse_args()
FIND_SUBTITLE = args.SEARCH

headers = {
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0'
}

# Create a PoolManager instance for HTTPS requests
https = urllib3.PoolManager(
    headers=headers,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
	timeout=5,
	retries=3
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

	# Save a copy of the original data
	search_data_complete = search_data

	# Limit the number of results displayed based on the user's preference
	if args.lines:
		result_limit = args.lines
	else:
		base_limit = 2 if args.compact else 3 if args.alternative else 5 if args.style and args.style.endswith('grid') else 10
		result_limit = base_limit + (1 if args.disable_help else 0)

	search_data = search_data[:result_limit]

	# Checking flag for switch to fast download mode
	if args.fast:
		id_subtitle = get_best_match(args, search_data_complete)
		get_subtitle(args, https, SUBDIVX_URL, id_subtitle)
		exit(0)

	# Initialize cache for comments
	if args.comments:
		cache_comments = TTLCache(capacity=len(search_data), ttl=60)

	# Pagination
	current_index = 0
	block_size = (result_limit if args.lines is None else args.lines)

	# Get the size of the complete data
	search_data_complete_size = len(search_data_complete)

	while True:
		# Clear screen
		clear()

		# Slice data
		search_data = search_data_complete[current_index:current_index + block_size]

		# Show Search Results
		if args.compact:
			print_search_results_compact(args, search_data)
		else:
			print_search_results(args, search_data)

		# Get the user selection
		if search_data_complete_size > block_size:

			# Show the pagination
			total_pages = (search_data_complete_size // block_size) + (search_data_complete_size % block_size > 0)
			current_page = (current_index // block_size) + 1
			page_info = f'[{current_page}/{total_pages}]'
			print(page_info.center(get_terminal_width()))

			user_input = prompt_user_selection(args, 'pagination')
		else:
			user_input = prompt_user_selection(args, 'subtitle')

		try:
			selection = int(user_input) - 1
			id_subtitle = str(search_data[selection]['id_subtitle'])
		except (ValueError, IndexError):
			if user_input.lower() == 'n':
				if current_index >= search_data_complete_size:
					current_index = search_data_complete_size - block_size
				elif current_index + block_size < search_data_complete_size:
					current_index += block_size
			elif user_input.lower() == 'p':
				current_index -= block_size
				if current_index < 0:
					current_index = 0
			else:
				print('\nInput only numbers')
				delay(0)
				continue
			clear()
			continue

		if selection < -1:
			print('\nInput only positive numbers')
			delay(0)
			continue
		elif selection == -1:
			clear()
			exit(0)

		clear()

		if args.alternative or args.compact:
			print_summary(args, selection, search_data)
		else:
			print_description(args, selection, search_data)

		# Checking flag for add comments view
		if args.comments:

			comment_from_cache = cache_comments.get(id_subtitle)

			if comment_from_cache and comment_from_cache != -1:
				helper.logger.info('Getting comments from cache')
				print_comments(args, comment_from_cache)
			else:
				comment_list = get_comments(https, SUBDIVX_URL, id_subtitle)
				cache_comments.put(id_subtitle, comment_list)

				if comment_list:
					print_comments(args, comment_list)

		# Show selection menu
		user_input = prompt_user_selection(args, 'download')

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
