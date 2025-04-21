# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import urllib3
import certifi

from .utils import *

SUBDIVX_URL = 'https://www.subdivx.com/'

args = helper.parser.parse_args()
SEARCH_TERM = parse_user_input(args.SEARCH)

rev = get_random_revision()

headers = {
    'user-agent': f'Mozilla/5.0 (X11; Linux x86_64; rv:{rev}) Gecko/20100101 Firefox/{rev}'
}

# Create a PoolManager instance for HTTPS requests
https = urllib3.PoolManager(
    headers=headers,
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
    timeout=5,
    retries=3
)

# Create a DataClient instance
data_client = DataClient(https, headers, SUBDIVX_URL)

# Delete data session if flag is set
if args.new_session:
	data_client.delete_data()

# Load or generate data session
if not data_client.has_data() or data_client.is_data_expired():
    data_client.generate_data()
    data_client.save_data()

data_session = data_client.get_data_session()

# Load configuration
config = Config().load_config() if args.load_config else {}
args = Args(args, config)

# Save configuration
if args.save_config:
    Config().save_config(args)

helper.logger.info(f'Arguments used: {args.get_args()}')

def main():
    # Get all data from search
    search_data = get_data_page(args, https, SUBDIVX_URL, data_session, SEARCH_TERM)

    # Sorting data if needed
    search_data = sort_data(args, search_data)

    # Checking flag for switch to fast download mode
    if args.fast:
        id_subtitle = get_best_match(args, search_data)
        get_subtitle(args, https, SUBDIVX_URL, id_subtitle)
        exit(0)

    # Size of the data
    search_data_size = len(search_data)

    # Initialize cache for comments
    if args.comments:
        cache_comments = TTLCache(capacity=search_data_size, ttl=120)

    # Reference to the original search data
    search_data_reference = search_data

    # Pagination current position
    current_index = 0

    # Save the initial maximum number of results
    initial_max_results = max_results_by_height(args)

    # Check if it has changed the screen
    resized = False

    while True:
        # Reset the current index if it has changed number of results to display
        current_max_results = max_results_by_height(args)
        if current_max_results != initial_max_results:
            if resized is False:
                current_index = 0
                resized = True
        elif current_max_results == initial_max_results:
            if resized is True:
                current_index = 0
                resized = False

        # Clear screen
        clear()

        # Limit the number of results displayed based on the user's preference
        result_limit = args.lines if args.lines else max_results_by_height(args)

        # Pagination
        block_size = args.lines if args.lines else result_limit

        # Slice data
        search_data = search_data_reference[current_index:current_index + block_size]

        # Show Search Results
        if args.compact:
            print_search_results_compact(args, search_data)
        else:
            print_search_results(args, search_data)

        # Get the user selection
        if search_data_size > block_size:

            # Show the pagination
            page_info = get_pagination_info(search_data_size, block_size, current_index)
            page_info_format = f'[{page_info["current_page"]}/{page_info["total_pages"]}]'
            terminal_width, _ = get_terminal_size()
            print(page_info_format.center(terminal_width))

        user_input = prompt_user_selection(args, 'pagination' if search_data_size > block_size else 'subtitle')

        try:
            selection = int(user_input) - 1
            id_subtitle = str(search_data[selection]['id_subtitle'])
        except (ValueError, IndexError):
            if user_input.lower() == 'n':
                if current_index >= search_data_size:
                    current_index = search_data_size - block_size
                elif current_index + block_size < search_data_size:
                    current_index += block_size
            elif user_input.lower() == 'p':
                current_index -= block_size
                if current_index < 0:
                    current_index = 0
            else:
                print_center_text('Input only valid numbers')
                continue
            clear()
            continue

        if selection < -1:
            print_center_text('Input only positive numbers')
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
        comments_selection = None

        if args.comments:
            comment_from_cache = cache_comments.get(id_subtitle)

            if comment_from_cache and comment_from_cache != -1:
                helper.logger.info('Getting comments from cache')
                comments_selection = paginate_comments(args, comment_from_cache, block_size, selection, search_data)
            else:
                comment_list = get_comments(https, SUBDIVX_URL, id_subtitle)
                cache_comments.put(id_subtitle, comment_list)

                if comment_list:
                    comments_selection = paginate_comments(args, comment_list, block_size, selection, search_data)

        # Show selection menu
        user_input = prompt_user_selection(args, 'download') if comments_selection is None else comments_selection

        try:
            select_action = int(user_input)
        except ValueError:
            print_center_text('Input only numbers')
            continue

        if select_action > 1 or select_action <= -1:
            print_center_text('Input valid numbers')
            continue
        elif select_action == 1:
            clear()
            get_subtitle(args, https, SUBDIVX_URL, id_subtitle)
            if args.no_exit:
                continue
            exit(0)
        elif select_action == 0:
            clear()
            exit(0)

if __name__ == '__main__':
    main()
