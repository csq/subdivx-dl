# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import asyncio

from subdivx_dl.utils import *
from subdivx_dl.translations.load_translations import get_translation, set_language

SUBDIVX_URL = 'https://www.subdivx.com/'

# Parse command-line arguments
args = helper.parser.parse_args()

# Load configuration
config = Config().load_config() if args.load_config else {}
args = Args(args, config)

# Set the language code if provided
set_language(args.language_code) if args.language_code else None

# Save configuration
Config().save_config(args) if args.save_config else None

helper.logger.info(f'Arguments used: {args.get_args()}')

# Parse user input
SEARCH_TERM = parse_user_input(args.SEARCH)

async def main_loop():

    # Get all data from search
    print(get_translation('init_browser'), end='\r')
    page = await Browser().open_page(SUBDIVX_URL)

    try:
        search_data = await get_data_page(args, page, SEARCH_TERM)
    except Exception:
        print(get_translation('error_retrieving_data'))
        await Browser().close_browser()
        DataSession().delete_data()
        sys.exit(1)

    # Sorting data if needed
    search_data = sort_data(args, search_data)

    # Checking flag for switch to fast download mode
    if args.fast:
        id_subtitle = get_best_match(args, search_data)
        await get_subtitle(args, page, id_subtitle)
        await Browser().close_browser()
        sys.exit(0)

    # Size of the data
    search_data_size = len(search_data)

    # Initialize cache for comments
    if args.comments:
        cache_comments = TTLCache(capacity=search_data_size, ttl=300)

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
                print_center_text(get_translation('input_only_valid_numbers'))
                continue
            clear()
            continue

        if selection < -1:
            print_center_text(get_translation('input_only_positive_numbers'))
            continue
        elif selection == -1:
            clear()
            await Browser().close_browser()
            sys.exit(0)

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
                comments_selection = paginate_comments(args, comment_from_cache, block_size, selection, search_data)
            else:
                comment_list = await get_comments(page, id_subtitle)
                cache_comments.put(id_subtitle, comment_list)

                if comment_list:
                    comments_selection = paginate_comments(args, comment_list, block_size, selection, search_data)

        # Show selection menu
        user_input = prompt_user_selection(args, 'download') if comments_selection is None else comments_selection

        try:
            select_action = int(user_input)
        except ValueError:
            print_center_text(get_translation('input_only_numbers'))
            continue

        if select_action > 1 or select_action <= -1:
            print_center_text(get_translation('input_valid_numbers'))
            continue
        elif select_action == 1:
            clear()
            await get_subtitle(args, page, id_subtitle)
            if args.no_exit:
                continue
            await Browser().close_browser()
            sys.exit(0)
        elif select_action == 0:
            clear()
            await Browser().close_browser()
            sys.exit(0)

async def run():
    try:
        await main_loop()
    except Exception as e:
        helper.logger.error(f'Unexpected error: {e}')
        await Browser().close_browser()
        sys.exit(1)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    main()
