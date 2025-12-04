# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import re
import sys
import json
import time
import shutil
import asyncio
import zipfile
import tempfile
import textwrap
import patoolib

from datetime import datetime
from tabulate import tabulate, SEPARATING_LINE
from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox
from guessit import guessit
from subdivx_dl import helper
from subdivx_dl.translations.load_translations import get_translation

SUBTITLE_EXTENSIONS = ('.srt', '.sub', '.ass', '.ssa', '.idx')

COMPRESSED_EXTENSIONS = ('.zip', '.rar', '.7z')

DEFAULT_STYLE = 'pretty'

def get_terminal_size():
    try:
        terminal_size = shutil.get_terminal_size()
        return terminal_size.columns, terminal_size.lines
    except OSError:
        return 80, 25

async def download_file(page, selected_index, dest_path):
    helper.logger.info('Downloading archive')

    selected_row = await page.wait_for_selector(f'table#resultados tbody tr[data-dt-row="{selected_index}"]')
    await selected_row.click()

    # Click download button
    download_selector = 'button#btnDescargar'
    async with page.expect_download() as download_info:
        await page.click(download_selector)

    download = await download_info.value

    await download.save_as(os.path.join(dest_path, download.suggested_filename))

def uncompress(compressed_path, dest_dir):
    try:
        helper.logger.info(f'Unpacking [{os.path.basename(compressed_path)}]')

        if compressed_path.endswith('.zip'):
            with zipfile.ZipFile(compressed_path, 'r') as zip_file:
                zip_file.extractall(dest_dir)
        else:
            patoolib.extract_archive(
                archive=compressed_path,
                outdir=dest_dir,
                interactive=False,
                verbosity=-1
            )
    except (zipfile.BadZipFile, patoolib.util.PatoolError) as e:
        helper.logger.error('Failed to unpack file')
        print(f'{get_translation("failed_to_unpack_file")} {e}')
        sys.exit(1)

def move_all_to_parent_directory(directory):
    for root, dirs, files in os.walk(directory, topdown=True):
        for dir_ in dirs:
            if dir_ != '__MACOSX':
                subdirectory = os.path.join(root, dir_)
                for _, _, filenames in os.walk(subdirectory, topdown=True):
                    for filename in filenames:
                        file_path = os.path.join(subdirectory, filename)
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in SUBTITLE_EXTENSIONS:
                            dest_path = os.path.join(directory, filename)
                            os.rename(file_path, dest_path)

def get_attribute_weights():
    attribute_weights = {
        'edition': 0.4,        # 40% importance
        'release_group': 0.25, # 25% importance
        'source': 0.2,         # 20% importance
        'screen_size': 0.05,   #  5% importance
        'video_codec': 0.05,   #  5% importance
        'size': 0.05           #  5% importance
    }

    return attribute_weights

def select_best_subtitle_from_list(args, data):
    helper.logger.info('Selecting the best subtitle from the list')

    guessit_info = DictCache().get()

    weights = get_attribute_weights()

    file_name = data[1][1]

    max_score = 0
    for i in range(1, len(data)):
        subtitle_name = data[i][1].strip().lower()

        score = 0
        for key in weights.keys():
            try:
                attribute = guessit_info[key].lower()

                if attribute in subtitle_name:
                    score += weights[key]
                    helper.logger.info(f'Found attribute [{key}] in subtitle [{i}]')
            except KeyError:
                pass

        if score > max_score:
            max_score = score
            file_name = data[i][1]
            helper.logger.info(f'New best match with score {max_score:.2f} in subtitle [{i}]')

    helper.logger.info(f'The best matching subtitle has been selected with a score {max_score:.2f}')
    return file_name

async def print_menu_content_dir(args, directory):
    header = [['N°', get_translation('file_name')]]

    file_names = [fname for fname in os.listdir(directory) if fname.endswith(SUBTITLE_EXTENSIONS)]
    file_count = len(file_names)

    for index, file_name in enumerate(file_names, start=1):
        header.append([index, file_name])

    if args.fast and file_count > 1:
        file_name = select_best_subtitle_from_list(args, header)
        return file_name

    if file_count > 1:
        while True:
            # Clear screen
            clear()

            # Print table with of the subtitles available
            print_centered(
                args,
                tabulate(
                    header, headers='firstrow', tablefmt=args.style or DEFAULT_STYLE, stralign='left'
                )
            )

            # Select subtitle
            user_input = prompt_user_selection(args, 'download')

            try:
                selection = int(user_input) - 1
                file_name = header[selection + 1][1]
            except (ValueError, IndexError):
                print_center_text(get_translation('input_valid_numbers'))
                continue

            if selection < -1:
                print_center_text(get_translation('input_only_positive_numbers'))
                continue
            elif selection == -1:
                # Remove temp directory
                try:
                    shutil.rmtree(directory)
                    helper.logger.info(f'Delete temporal directory {directory}')
                except OSError as error:
                    helper.logger.error(error)
                clear()
                await Browser().close_browser()
                sys.exit(0)

            # Return the file_name of the selected subtitle file
            clear()
            return file_name
    else:
        # Return the file_name of the subtitle
        return file_names[0]

def rename_subtitle_file(source_file_path, dest_file_path):
    try:
        # Create destination directory if not exists
        os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

        # Move the file
        shutil.move(source_file_path, dest_file_path)
    except (PermissionError, FileExistsError) as error:
        helper.logger.warning(f'Permissions issues on destination directory: {error}')
        print(f'{get_translation("error_occurred")} {error}')
        sys.exit(0)

async def rename_and_move_subtitle(args, source_dir, dest_dir):
    subtitle_files = [
        file for file in os.listdir(source_dir)
        if file.endswith(SUBTITLE_EXTENSIONS)
    ]

    for source_file in subtitle_files:
        extension = os.path.splitext(source_file)[1]
        num_subtitles = len(subtitle_files)

        if args.no_rename and not args.season:
            if num_subtitles > 1:
                selected_subtitle = await print_menu_content_dir(args, source_dir)
                source_file_path = os.path.join(source_dir, selected_subtitle)
                dest_file_path = os.path.join(dest_dir, selected_subtitle)

                helper.logger.info(f'Move [{selected_subtitle}] to {dest_dir} as [{selected_subtitle}]')
                rename_subtitle_file(source_file_path, dest_file_path)
                break
            elif num_subtitles == 1:
                dest_file = source_file
        elif args.no_rename and args.season:
            dest_file = source_file
        elif args.season:
            subtitle_data = guessit(source_file)
            if subtitle_data['type'] == 'episode':
                series = subtitle_data.get('title', '')
                season = f'S{subtitle_data["season"]:02d}'
                try:
                    episode = f'E{subtitle_data["episode"]:02d}'
                except (KeyError, ValueError):
                    episode = f'E{subtitle_data["episode"][0]:02d}-E{subtitle_data["episode"][1]:02d}'
                dest_file = f'{series} - {season}{episode}{extension}' if series else f'{season}{episode}{extension}'
            else:
                movie_name = subtitle_data['title']
                year = subtitle_data['year']
                dest_file = f'{movie_name} ({year}){extension}' if year else f'{movie_name}{extension}'
        else:
            dest_file = os.path.splitext(args.SEARCH)[0].strip() + extension

            if num_subtitles > 1:
                selected_subtitle = await print_menu_content_dir(args, source_dir)
                source_file_path = os.path.join(source_dir, selected_subtitle)

                # Get subtitle extension from selected subtitle
                subtitle_extension = os.path.splitext(selected_subtitle)[1]
                dest_file_path = os.path.join(dest_dir, dest_file.replace(extension, subtitle_extension))

                helper.logger.info(f'Move [{selected_subtitle}] to {dest_dir} as [{dest_file}]')
                rename_subtitle_file(source_file_path, dest_file_path)
                break

        # Find IMDb code in search term
        pattern = r'\btt\d{7,8}\b'
        imdb_code = re.search(pattern, args.SEARCH)

        if imdb_code:
            dest_file = source_file

        source_file_path = os.path.join(source_dir, source_file)
        dest_file_path = os.path.join(dest_dir, dest_file)

        helper.logger.info(f'Move [{source_file}] to {dest_dir} as [{dest_file}]')
        rename_subtitle_file(source_file_path, dest_file_path)

def rename_file_extension(directory):
    for filename in os.listdir(directory):
        # Split filename into name and extension
        name, ext = os.path.splitext(filename)

        # Check if the file has a subtitle extension
        if ext.lower() in SUBTITLE_EXTENSIONS:
            # If the extension is upper-case, rename the file to lower-case
            if ext.isupper():
                new_filename = f'{name}{ext.lower()}'
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))

async def get_data_page(args, page, search_term):
    clear()
    print(get_translation('searching'), end='\r')

    # Save guessit info to cache
    guessit_info = GuessitInfo(search_term).get_info()
    DictCache().store(guessit_info)

    query = guessit_info['title']
    helper.logger.info(f'Searching subtitle for: {query}')

    # Locate Search box
    search_box = page.locator('#buscar')
    await search_box.wait_for()
    await search_box.click()
    await search_box.fill(query)
    await search_box.press('Enter')

    # List all of results
    selector = page.locator('#dt-length-0')
    await selector.wait_for()
    await selector.click()
    await selector.select_option('Todas')
    await selector.press('Escape')

    # Save results in json file
    results_list = []

    try:
        await page.wait_for_selector('table#resultados tbody tr.trMarcar', state='visible', timeout=5000)
        rows = await page.query_selector_all('table#resultados tbody tr.trMarcar.dt-hasChild.dtr-expanded')

        for index, row in enumerate(rows, start=0):
            title = await row.query_selector('td:nth-child(2) span')
            title_text = await title.inner_text()

            description = await row.query_selector('td:nth-child(3)')
            description_text = await description.inner_text()

            downloads = await row.query_selector('td:nth-child(4)')
            downloads_text = await downloads.inner_text()

            user = await row.query_selector('td:nth-child(8) a')
            user_text = await user.inner_text()

            date = await row.query_selector('td:nth-child(9)')
            date_text = await date.inner_text()
            match = re.search(r'\d{2}/\d{2}/\d{4}', date_text)
            date_text = match.group(0) if match and match.group(0) != '00/00/0000' else '-'

            # Create JSON-like dictionary
            data_entry = {
                'id_subtitle': index,
                'title': title_text,
                'description': description_text,
                'downloads': downloads_text,
                'uploader': user_text,
                'upload_date': date_text
            }

            # Append to the results list
            results_list.append(data_entry)

    except Exception:
        await Browser().close_browser()
        if not args.verbose:
            print(get_translation('no_subtitles_found'))
        helper.logger.info(f'No subtitles found for query: {search_term}')
        sys.exit(0)

    helper.logger.info(f'Found subtitles for query: {search_term}')
    return results_list

def sort_data(args, data):
    if args.order_by_downloads:
        return sorted(data, key=lambda item: item['downloads'], reverse=True)
    elif args.order_by_dates:
        return sorted(
            data,
            key=lambda item: (
                datetime.strptime(item['upload_date'], '%d/%m/%Y'
                if item['upload_date'] != '-' else '-')
            ),
            reverse=True
        )
    else:
        return data

def parse_user_input(input):
    search = input.strip()
    if search == '':
        print(get_translation('invalid_search_try_again'))
        helper.logger.error('Invalid search')
        sys.exit(0)
    return search

run_get_comments = 1
async def get_comments(page, subtitle_id):
    global run_get_comments

    # Select subtitle
    selected_row = await page.wait_for_selector(f'table#resultados tbody tr[data-dt-row="{subtitle_id}"]')
    await selected_row.click()

    # List all of comments
    select = page.locator(f'#dt-length-{run_get_comments}')
    await select.wait_for()
    await select.click()
    await select.select_option('100')

    # Select table comments
    comments_data = []
    rows = await page.query_selector_all('#tblComentarios tbody tr')
    for row in rows:
        cells = await row.query_selector_all('td')
        if len(cells) != 3:
            continue

        comment = (await cells[0].inner_text()).strip()
        comments_data.append({'comment': comment})

    comments = [comment['comment'] for comment in comments_data]

    # Close modal
    btn_close = page.locator('#modalDetailDown .btn-close')
    await btn_close.click()

    run_get_comments += 1

    return comments

def print_search_results(args, search_data):
    terminal_width, _ = get_terminal_size()

    maxcolwidths = []

    # Check flag --minimal
    if args.minimal:
        columns = ['N°', 'title', 'downloads', 'date']
        align = ['center', 'center', 'decimal', 'center']
        min_width = 40

    elif args.alternative:
        columns = ['N°', 'title', 'description']
        align = ['center', 'center', 'left']
        maxcolwidths = [None, terminal_width // 3,  terminal_width // 2]

    else:
        columns = ['N°', 'title', 'downloads', 'date', 'user']
        align = ['center', 'center', 'decimal', 'center', 'center']
        min_width = 55

    # Translate columns
    translated_columns = []

    for column_name in columns:
        translated_column = get_translation(column_name)

        if column_name == 'N°':
            translated_column = column_name
        elif column_name == 'downloads':
            translated_column = translated_column.ljust(11) if args.style else translated_column
        elif column_name == 'description':
            translated_column = translated_column.center(terminal_width // 2)

        translated_columns.append(translated_column)

    table_data = [translated_columns]

    for index, item in enumerate(search_data, start=1):

        if args.alternative:
            table_data.append([
                index,
                item['title'],
                item['description']
            ][:len(columns)])

            if index < len(search_data) and (not args.style.endswith('grid') if args.style else True):
                table_data.append(SEPARATING_LINE)
        else:
            title = shorten_text(item['title'], terminal_width - min_width)
            table_data.append([
                index,
                title,
                item['downloads'],
                item['upload_date'],
                item.get('uploader', '')
            ][:len(columns)])

    # Print the centered table
    print_centered(
        args,
        tabulate(
            table_data, headers='firstrow', tablefmt=args.style or DEFAULT_STYLE, colalign=align, maxcolwidths=maxcolwidths
        )
    )

def max_results_by_height(args):
    _, terminal_height = get_terminal_size()

    # Lines excluded (empty line, header and help messages)
    min_lines_excluded = 8
    max_lines_excluded = 10

    # Default values
    lines_to_exclude = min_lines_excluded if args.disable_help else max_lines_excluded
    max_results = (terminal_height - lines_to_exclude)

    if args.style:
        if args.style in ['presto', 'simple', 'pipe', 'orgtbl']:
            lines_to_exclude = 6 if args.disable_help else 9
            max_results = (terminal_height - lines_to_exclude)
        elif args.style.endswith('grid'):
            single_line_height = 2
            max_results = (terminal_height - lines_to_exclude) // single_line_height

    if args.alternative:
        single_line_height = 3
        max_results = (terminal_height - lines_to_exclude) // single_line_height
    elif args.compact:
        single_line_height = 5
        max_results = (terminal_height - lines_to_exclude) // single_line_height

    return max_results

def print_search_results_compact(args, search_data):
    terminal_width, _ = get_terminal_size()

    table_data = []

    maxcolwidths = [None, terminal_width - 12]
    align = ['center', 'left']

    for index, item in enumerate(search_data, start=1):

        table_data.append([index, item['title'].center(terminal_width - 12)])
        table_data.append([None, item['description']])

        styles = ['presto', 'simple', 'pipe', 'orgtbl']

        # Print the centered table
        print_centered(
            args,
            tabulate(
                table_data, headers='firstrow', tablefmt=args.style or DEFAULT_STYLE, colalign=align, maxcolwidths=maxcolwidths
            ), end=('\n\n' if args.style in styles else '\n')
        )

        table_data.clear()

def print_centered(args, text, end=None):
    terminal_width, _ = get_terminal_size()

    if args.style in ['simple', 'presto']:
        first_line_length = len(text.splitlines()[1])
    else:
        first_line_length = len(text.splitlines()[0])

    padding_width = (terminal_width - first_line_length) // 2

    centered_lines = [' ' * padding_width + line for line in text.splitlines()]
    centered_text = '\n'.join(centered_lines)

    print('\n' + centered_text, end=end)

def shorten_text(text, width):
    placeholder = '...'

    if width <= len(placeholder):
        width = len(placeholder)

    return textwrap.shorten(text, width=width, placeholder=placeholder)

def print_center_text(text):
    terminal_width, terminal_height = get_terminal_size()

    padding = '\n' * ((terminal_height // 2) - 5)

    clear()
    print(padding + text.center(terminal_width))
    time.sleep(0.8)

def print_description(args, selection, search_data):
    terminal_width, _ = get_terminal_size()
    description = search_data[selection]['description'].strip()

    description_text = get_translation('description').center(terminal_width - 8)
    description_table = [[description_text], [description]]

    print_centered(
        args,
        tabulate(
            description_table,
            headers='firstrow',
            tablefmt=args.style or DEFAULT_STYLE,
            stralign='left',
            maxcolwidths=[terminal_width - 8]
        ), end=('\n\n' if args.style in ['presto', 'simple', 'pipe', 'orgtbl'] else '\n')
    )

def print_summary(args, selection, search_data):
    terminal_width, _ = get_terminal_size()

    summary = []

    attributes = ['title', 'downloads', 'upload_date', 'uploader']
    for attribute in attributes:
        attribute_text = get_translation(attribute)
        summary.append([attribute_text.capitalize(), search_data[selection][attribute]])

    print_centered(
        args,
        tabulate(
            summary,
            headers='firstrow',
            tablefmt=args.style or DEFAULT_STYLE,
            stralign='left',
            maxcolwidths=[terminal_width - 5]
        ), end=('\n\n' if args.style in ['presto', 'simple', 'pipe', 'orgtbl'] else '\n')
    )

async def get_subtitle(args, page, selected_index):
    if not args.verbose:
        print(get_translation('working'), end='\r')

    # Create temporal directory
    with tempfile.TemporaryDirectory() as temp_dir:
        helper.logger.info(f'Create temporal directory {temp_dir}')

        # Download file compressed in temporal directory
        await download_file(page, selected_index, temp_dir)

        # Extract files, including nested archives, up to depth 2
        excluded_file_names = set()

        max_extraction_depth = 2

        while max_extraction_depth > 0:
            for file_name in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file_name)

                if file_name.endswith(COMPRESSED_EXTENSIONS) and file_name not in excluded_file_names:
                    uncompress(file_path, temp_dir)
                    excluded_file_names.add(file_name)

            max_extraction_depth -= 1

        # Move all files from any subdirectories to the parent directory
        move_all_to_parent_directory(temp_dir)

        # Rename file extension if necessary
        rename_file_extension(temp_dir)

        # Get destination directory
        dest_dir = args.location or os.getcwd()

        # Rename and/or move subtitles
        await rename_and_move_subtitle(args, temp_dir, dest_dir)

    # Message for user
    helper.logger.info(f'Delete temporal directory {temp_dir}')

    if not args.verbose:
        clear()
        print(get_translation('done'))

def are_titles_equal(media_info_a, media_info_b):
    # Extract normalized titles
    titles1 = {
        media_info_a.get('title'),
        media_info_a.get('alternative_title')
    }

    titles2 = {
        media_info_b.get('title'),
        media_info_b.get('alternative_title')
    }

    # Check for any intersection between title sets
    return bool(titles1 & titles2)

def titles_have_common_word(title_1, title_2):
    # Split strings into words
    words1 = set(title_1.lower().split())
    words2 = set(title_2.lower().split())

    # Check if there's at least two words in common
    return len(words1.intersection(words2)) >= 2

def get_best_match(args, search_data):
    helper.logger.info('Finding the best match subtitle')

    media_info = DictCache().get()

    weights = get_attribute_weights()

    id_subtitle = search_data[0]['id_subtitle']
    previous_subtitle_title = None

    max_score = 0

    # Iterate over all subtitles to find the best match
    for subtitle in search_data:
        subtitle_title = subtitle['title'].strip().lower()

        # Extract title info only once
        if subtitle_title != previous_subtitle_title:
            previous_subtitle_title = subtitle_title
            subtitle_title = clean_text(subtitle_title)
            subtitle_guessit_info = GuessitInfo(subtitle_title).get_info()

        # Check for exact title matches or common words in the title
        if (
            are_titles_equal(media_info, subtitle_guessit_info)
            or (max_score == 0 and titles_have_common_word(media_info['title'], subtitle_guessit_info['title']))
        ):
            # If there's no previous best match, take the first subtitle
            if max_score == 0 and 'forzado' not in subtitle['title'].lower():
                id_subtitle = subtitle['id_subtitle']

            # Identify matches in the description field
            subtitle_description = subtitle['description'].replace('Blu-Ray', 'BluRay').lower()
            subtitle_description = subtitle_description.replace('director\'s', 'directors')

            score = 0
            for key in weights.keys():
                try:
                    attribute = media_info[key].lower()

                    if attribute in subtitle_description:
                        score += weights[key]
                        helper.logger.info(f'Found attribute [{key}] in subtitle [{subtitle["id_subtitle"]}]')
                except KeyError:
                    pass

            if score > max_score:
                max_score = score
                id_subtitle = subtitle['id_subtitle']
                helper.logger.info(f'New best match with score {max_score:.2f} in subtitle [{id_subtitle}]')

    helper.logger.info(f'Returning the best match for {args.SEARCH} is subtitle [{id_subtitle}] with score {max_score:.2f}')
    return id_subtitle

def print_comments(args, comments):
    terminal_width, _ = get_terminal_size()

    base_padding = 5
    if args.style:
        if args.style.endswith('grid') or args.style in ['presto', 'pipe', 'orgtbl', 'psql']:
            base_padding = 7
        elif args.style in ['rst', 'simple']:
            base_padding = 8

    label_width = 6 if args.style in ['simple', 'rst'] else 8
    comment_text = get_translation('comment')
    comment_label = comment_text.center(terminal_width - base_padding)[label_width:]

    table = [['N°', comment_label]]
    for index, comment in enumerate(comments, start=1):
        table.append([index, comment])

    tablefmt = args.style or DEFAULT_STYLE
    colalign = ['center', 'left']
    maxcolwidths = [None, terminal_width - 15]

    print_centered(
        args,
        tabulate(
            table, headers='firstrow', tablefmt=tablefmt, colalign=colalign, maxcolwidths=maxcolwidths
        ), end=('\n\n' if args.style in ['presto', 'simple', 'pipe', 'orgtbl'] else '\n')
    )

def get_pagination_info(list_size, block_size, current_index):
    total_pages = (list_size // block_size) + (list_size % block_size > 0)
    current_page = (current_index // block_size) + 1
    page_info = {
        'current_page': current_page,
        'total_pages': total_pages
    }
    return page_info

def paginate_comments(args, comments_list, block_size=10, selection=None, description_list=None):
    comments_list_length = len(comments_list)
    current_index = 0

    # Data pagination
    page_info = get_pagination_info(comments_list_length, block_size, current_index)

    current_page = page_info['current_page']
    total_pages = page_info['total_pages']

    while current_page <= total_pages:
        start_index = current_index
        end_index = min(current_index + block_size, comments_list_length)
        page_comments = comments_list[start_index:end_index]

        clear()

        if args.alternative or args.compact:
            print_summary(args, selection, description_list)
        else:
            print_description(args, selection, description_list)

        print_comments(args, page_comments)

        if total_pages > 1:
            page_info_format = f'[{current_page}/{total_pages}]'
            terminal_width, _ = get_terminal_size()
            print(page_info_format.center(terminal_width))

        user_input = prompt_user_selection(args, 'comments' if total_pages > 1 else 'download')

        # Menu pagination
        if total_pages >= 1:
            if user_input.lower() == 'n' and total_pages > 1:
                if current_page == total_pages:
                    current_page = total_pages
                else:
                    current_page += 1
            elif user_input.lower() == 'p' and total_pages > 1:
                if current_page == 1:
                    current_page = 1
                elif current_page > 1:
                    current_page -= 1
            else:
                return user_input
            current_index = (current_page - 1) * block_size
            page_info = f'[{current_page}/{total_pages}]'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def prompt_user_selection(args, menu_name: str, options: list = ['subtitle', 'download', 'pagination']):
    terminal_width, _ = get_terminal_size()
    padding = ' ' * ((terminal_width // 2) - 6)

    exit_text = get_translation('exit')
    selec_text = get_translation('select')
    download_text = get_translation('download')
    next_page_text = get_translation('next_page')
    previous_page_text = get_translation('previous_page')

    main_menu = f'[1-9] {selec_text} [ 0 ] {exit_text}'.center(terminal_width)
    secondary_menu = f'[ 1 ] {download_text} [ 0 ] {exit_text}'.center(terminal_width)
    paginate_menu = f'[ n ] {next_page_text} [ p ] {previous_page_text}'.center(terminal_width)

    menu_options = {
        'subtitle': main_menu,
        'pagination': main_menu + '\n' + paginate_menu,
        'download': secondary_menu,
        'comments': secondary_menu + '\n' + paginate_menu
    }[menu_name]

    if not args.disable_help:
        print('\n' + menu_options.center(terminal_width))

    try:
        user_input = input('\n' + padding + get_translation('selection'))
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)

    return user_input

# -- Class Args -- #
class Args():
    def __init__(self, args=None, config=None):
        super().__init__()

        self.SEARCH = None

        if args is not None:
            for key, value in args.__dict__.items():
                setattr(self, key, value)

        if config is not None:
            for key, value in config.items():
                setattr(self, key, value)
            self.SEARCH = args.SEARCH

    def get_args(self):
        arguments = []

        for attribute, value in self.__dict__.items():
            if attribute != 'SEARCH' and value is not False and value is not None:
                arguments.append(f'{attribute}={value}')

        return arguments

# -- Class Config -- #
class Config():
    _CONFIG_FILE_NAME = 'config.json'

    def __init__(self):
        self.config_directory = self._create_config_directory()
        self.config_path = os.path.join(self.config_directory, self._CONFIG_FILE_NAME)

    def _create_config_directory(self):
        import platform
        platform_name = platform.system()

        local_appdata = os.getenv('LOCALAPPDATA')

        directory_paths = {
            'Linux': '~/.config/subdivx-dl/',
            'Darwin': '~/Library/Application Support/subdivx-dl/',
            'Windows': f'{local_appdata}\\subdivx-dl\\'
        }

        config_directory = os.path.expanduser(directory_paths[platform_name])
        os.makedirs(config_directory, exist_ok=True)

        return config_directory

    def save_config(self, args):
        args_copy = args.__dict__.copy()

        # Remove keys that are not needed in the config file
        keys_to_remove = {'SEARCH', 'load_config', 'save_config', 'check_update'}

        # Remove keys that have empty values
        keys_to_remove.update(key for key, value in args_copy.items() if not value)

        # Remove the identified keys
        for key in keys_to_remove:
            args_copy.pop(key, None)

        with open(self.config_path, 'w') as file:
            json.dump(args_copy, file, indent=4, sort_keys=True)

        helper.logger.info(f'Save configuration file {self.config_path}')

    def load_config(self):
        if not os.path.exists(self.config_path):
            helper.logger.info('Not found configuration file, usage default values')
            return {}

        with open(self.config_path, 'r') as file:
            helper.logger.info(f'Load configuration file {self.config_path}')
            return json.load(file)

# -- Class TTLCache -- #
# See: https://medium.com/@denis.volokh/caching-methods-implementations-and-comparisons-in-python-7d29a2b0cd80

class TTLCache:
    def __init__(self, capacity, ttl):
        # Initialize the TTLCache with a given capacity and time-to-live (ttl)
        self.capacity = capacity
        self.ttl = ttl
        # cache stores the key-value pairs
        self.cache = {}
        # timestamps stores the time when each key was added or last updated
        self.timestamps = {}

    def get(self, key):
        # Retrieve the value associated with 'key' if it hasn't expired
        if key in self.cache:
            # Check if the key has expired by comparing current time with its timestamp
            if time.time() - self.timestamps[key] < self.ttl:
                # Return the value if it's still valid
                return self.cache[key]
            else:
                # If the key has expired, remove it from cache and timestamps
                del self.cache[key]
                del self.timestamps[key]
        # Return -1 if the key is not found or has expired
        return -1

    def put(self, key, value):
        # Add or update a key-value pair in the cache
        if len(self.cache) >= self.capacity and key not in self.cache:
            # Evict items if the cache is full and the key is not already present
            self.evict()
        # Store the value in the cache and record the current timestamp
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def evict(self):
        # Evict expired items from the cache
        current_time = time.time()
        # Find all keys that have expired
        expired = [k for k, t in self.timestamps.items() if current_time - t >= self.ttl]
        for key in expired:
            # Remove expired keys from cache and timestamps
            del self.cache[key]
            del self.timestamps[key]
        if not expired and self.cache:
            # If no expired items are found, evict the oldest item in the cache
            oldest = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest]
            del self.timestamps[oldest]

def clean_text(text):
    aka_pattern = r'\b(a\s*\.?\s*k\s*\.?\s*a\.?\.?|A\s*\.?\s*K\s*\.?\s*A\.?\.?)\b'
    text = re.sub(aka_pattern, 'aka', text, flags=re.IGNORECASE)
    text = text.replace(':', '')
    return re.sub(r'\s+', ' ', text).strip()

# -- Class GuessitInfo -- #
class GuessitInfo:
    _SHARED_INFO = None

    def __init__(self, search_term):
        if self._SHARED_INFO is None:
            guessit_info = guessit(search_term)
            self._SHARED_INFO = self._process_info(guessit_info)

    def _parse_info(self, guessit_info):
        film = guessit_info.get('film')
        if film:
            guessit_info['title'] = f'F{film} {guessit_info.get("title", "")}'

        title = clean_text(guessit_info.get('title'))
        if title:
            # Extract title and alternative title if 'aka' is present
            aka_index = title.lower().find('aka')
            if aka_index != -1:
                alternative_title_start_index = aka_index + 4
                guessit_info['title'] = clean_text(title[:aka_index])
                guessit_info['alternative_title'] = clean_text(title[alternative_title_start_index:])

        source = guessit_info.get('source')
        if source:
            guessit_info['source'] = source.replace('Blu-ray', 'BluRay')

        video_codec = guessit_info.get('video_codec')
        if video_codec:
            guessit_info['video_codec'] = video_codec.replace('H.', '')

        size = guessit_info.get('size')
        if size:
            guessit_info['size'] = str(size)

        edition = guessit_info.get('edition')
        if edition:
            guessit_info['edition'] = edition.replace('Director\'s', 'Directors')

        alternative_title = guessit_info.get('alternative_title')
        if alternative_title:
            list_title = []

            try:
                alternative_title = clean_text(alternative_title)
                aka_index = alternative_title.lower().find('aka')
            except(TypeError, AttributeError):
                for title in alternative_title:
                    title = clean_text(title)
                    aka_index = title.lower().find('aka')
                    if aka_index != -1:
                        alternative_title_start_index = aka_index + 4
                        list_title.append(title[alternative_title_start_index:])
                guessit_info['alternative_title'] = list_title

            if aka_index != -1:
                alternative_title_start_index = aka_index + 4
                guessit_info['alternative_title'] = alternative_title[alternative_title_start_index:]

        return guessit_info

    def _format_name_media(self, guessit_info):
        media_info = {}

        if guessit_info['type'] == 'episode':
            try:
                episode_number = f'E{guessit_info.get("episode"):02d}' if guessit_info.get('episode') else ''
            except TypeError:
                episode_number = f'E{guessit_info.get("episode")[0]:02d}'
            media_info['title'] = f'{guessit_info.get("title")} S{guessit_info.get("season"):02d}{episode_number}'
            media_info['alternative_title'] = f'{guessit_info.get("episode_title")}' if guessit_info.get('episode_title') else media_info['title']
        else:
            media_info['title'] = f'{guessit_info.get("title")} ({guessit_info.get("year")})' if guessit_info.get('year') else guessit_info['title']
            alternative_title = guessit_info.get('alternative_title', '')
            media_info['alternative_title'] = (f'{alternative_title} ({guessit_info.get("year")})' if alternative_title else guessit_info.get('title'))

        return media_info

    def _process_info(self, guessit_info):
        parsed_info = self._parse_info(guessit_info)
        formatted_info = self._format_name_media(parsed_info)

        white_list = ['edition', 'release_group', 'source', 'screen_size', 'video_codec', 'size']
        for key, value in parsed_info.items():
            if key in white_list:
                formatted_info[key] = value

        return formatted_info

    def get_info(self):
        return self._SHARED_INFO

# -- Class DictCache -- #
class DictCache:
    _instance = None
    _cache = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DictCache, cls).__new__(cls)
        return cls._instance

    def store(self, dictionary):
        self._cache = dictionary

    def get(self):
        return self._cache

# -- Class DataSession -- #
class DataSession():
    _PATH_DATA = os.path.join(tempfile.gettempdir(), 'subdivx-dl')

    def delete_data(self):
        if self.has_data():
            helper.logger.info('Delete data session')
            shutil.rmtree(self._PATH_DATA)

    def has_data(self):
        return os.path.exists(self._PATH_DATA)

# -- Class Browser -- #
class Browser:
    _instance = None
    _user_data_dir = os.path.join(tempfile.gettempdir(), 'subdivx-dl', 'user_data')

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Browser, cls).__new__(cls)
            cls._instance.browser = None
        return cls._instance

    async def _get_browser(self):
        if self.browser is None:
            self.browser = AsyncCamoufox(
                headless=True,
                os=['macos'],
                screen=Screen(max_width=1920, max_height=1080),
                persistent_context=True,
                user_data_dir=Browser._user_data_dir
            )
            await self.browser.start()
        return self.browser.browser

    # See: https://github.com/MaestroOfAutomation/turnstile_bypass
    async def _cloudflare_bypass(self, url: str):
        browser = await self._get_browser()
        page = await browser.new_page()
        await page.goto(url)

        try:
            for _ in range(15):
                await asyncio.sleep(1)

                for frame in page.frames:
                    if frame.url.startswith('https://challenges.cloudflare.com'):
                        frame_element = await frame.frame_element()
                        bounding_box = await frame_element.bounding_box()
                        coord_x = bounding_box['x']
                        coord_y = bounding_box['y']

                        width = bounding_box['width']
                        height = bounding_box['height']

                        checkbox_x = coord_x + width / 9
                        checkbox_y = coord_y + height / 2

                        await page.mouse.click(x=checkbox_x, y=checkbox_y)
        except Exception:
            helper.logger.error('Error bypassing Cloudflare')
            return page

        helper.logger.info('Bypassed Cloudflare')
        return page

    async def open_page(self, url: str):
        try:
            if os.path.exists(Browser._user_data_dir) is False:
                page = await self._cloudflare_bypass(url)
            else:
                browser = await self._get_browser()
                page = await browser.new_page()
                await page.goto(url)
        except Exception:
            print(get_translation('error_starting_browser'))
            helper.logger.error('Not started browser')
            sys.exit(1)
        else:
            helper.logger.info('Started browser')
            return page

    async def close_browser(self):
        if self.browser is not None:
            await self.browser.browser.close()
            self.browser = None
            helper.logger.info('Closed browser')
