# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import re
import json
import time
import random
import shutil
import tempfile
import textwrap
import platform

from json import JSONDecodeError
from urllib3.exceptions import ProtocolError, MaxRetryError, TimeoutError
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from tabulate import tabulate, SEPARATING_LINE
from zipfile import ZipFile
from rarfile import RarFile
from guessit import guessit
from subdivx_dl import helper

SUBTITLE_EXTENSIONS = ('.srt', '.sub', '.ass', '.ssa', '.idx')

DEFAULT_STYLE = 'pretty'

def get_terminal_size():
    try:
        terminal_size = shutil.get_terminal_size()
        return terminal_size.columns, terminal_size.lines
    except OSError:
        return 80, 25

def get_file_extension(file_path):
    with open(file_path, 'rb') as file:
        header = file.read(4)

    file_signatures = {
        b'\x50\x4B\x03\x04': '.zip',
        b'\x52\x61\x72\x21': '.rar'
    }

    for signature, extension in file_signatures.items():
        if header.startswith(signature):
            return extension

    return '.bin' # For unknown file

def download_file(poolManager, url, id_subtitle, location):
    helper.logger.info(f'Downloading archive from: {url}{id_subtitle} in {location}')

    success = False

    with NamedTemporaryFile(dir=location, delete=False) as temp_file:
        for i in range(9, 0, -1):
            server_address = f'{url}sub{i}/{id_subtitle}'
            helper.logger.info(f'Attempt on server N°{i} with url {server_address}')

            response = https_request(poolManager, 'GET', server_address)

            temp_file.write(response.data)
            temp_file.seek(0)

            file_extension = get_file_extension(temp_file.name)

            if file_extension != '.bin':
                helper.logger.info('Download complete')
                temp_file.close()

                temp_file_new_name = f'{temp_file.name}{file_extension}'
                os.rename(temp_file.name, temp_file_new_name)

                success = True
                break

    if not success:
        print('No subtitles were downloaded because the link is broken')
        helper.logger.error(f'Subtitles not downloaded, link broken: {url}{id_subtitle}')
        exit(1)

def unzip(zip_file_path, dest_dir):
    try:
        with ZipFile(zip_file_path, 'r') as z:
            helper.logger.info(f'Unpacking zip [{os.path.basename(z.filename)}]')
            for file in z.namelist():
                if file.lower().endswith(SUBTITLE_EXTENSIONS):
                    helper.logger.info(f'Unzip [{os.path.basename(file)}]')
                    z.extract(file, dest_dir)
    except Exception as e:
        helper.logger.error('Failed to unzip file')
        print(f'Failed to unzip file: error {e}')
        exit(1)

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

def unrar(rar_file_path, dest_dir):
    helper.logger.info(f'Unpacking rar [{os.path.basename(rar_file_path)}] in {dest_dir}')
    rf = RarFile(rar_file_path)

    for file in rf.namelist():
        if file.lower().endswith(SUBTITLE_EXTENSIONS):
            helper.logger.info(f'Unrar [{os.path.basename(file)}]')
            rf.extract(file, dest_dir)
    rf.close()

def get_attribute_weights():
    attribute_weights = {
        'source': 0.5,         # 50% importance
        'release_group': 0.25, # 25% importance
        'screen_size': 0.1,    # 10% importance
        'video_codec': 0.05,   #  5% importance
        'size': 0.05,          #  5% importance
        'other': 0.05          #  5% importance
    }

    return attribute_weights

def select_best_subtitle_from_list(args, data):
    helper.logger.info('Selecting the best subtitle from the list')

    key_values = guessit(args.SEARCH)
    normalized_key_values = normalize_key_values(key_values)

    weights = get_attribute_weights()

    max_score = 0

    file_name = ''
    first_file = data[1][1]

    for i in range(1, len(data)):
        # Search match text with name of subtitle
        score = 0
        for key in weights.keys():
            try:
                subtitle_name = data[i][1].strip().lower()
                attribute = normalized_key_values[key].lower()

                if attribute in subtitle_name:
                    score += weights[key]
                    helper.logger.info(f'Found attribute [{key}] in subtitle [{i}]')
            except KeyError:
                pass

        if max_score < score:
            max_score = score
            file_name = data[i][1]
            helper.logger.info(f'New best match with score {max_score:.2f} in subtitle [{i}]')

    if max_score > 0:
        helper.logger.info(f'The best matching subtitle has been selected with a score {max_score:.2f}')
        return file_name
    else:
        helper.logger.info('The first available subtitle has been selected')
        return first_file

def print_menu_content_dir(args, directory):
    header = [['N°', 'File name']]

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
                print_center_text('Input valid numbers')
                continue

            if selection < -1:
                print_center_text('Input only positive numbers')
                continue
            elif selection == -1:
                # Remove temp directory
                try:
                    shutil.rmtree(directory)
                    helper.logger.info(f'Delete temporal directory {directory}')
                except OSError as error:
                    helper.logger.error(error)
                clear()
                exit(0)

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
        print(f'An error has occurred: {error}')
        exit(0)

def rename_and_move_subtitle(args, source_dir, dest_dir):
    subtitle_files = [
        file for file in os.listdir(source_dir)
        if file.endswith(SUBTITLE_EXTENSIONS)
    ]

    for source_file in subtitle_files:
        extension = os.path.splitext(source_file)[1]
        num_subtitles = len(subtitle_files)

        if args.no_rename and not args.season:
            if num_subtitles > 1:
                selected_subtitle = print_menu_content_dir(args, source_dir)
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
            dest_file = str(args.SEARCH).strip() + extension

            if num_subtitles > 1:
                selected_subtitle = print_menu_content_dir(args, source_dir)
                source_file_path = os.path.join(source_dir, selected_subtitle)
                dest_file_path = os.path.join(dest_dir, dest_file)

                helper.logger.info(f'Move [{selected_subtitle}] to {dest_dir} as [{dest_file}]')
                rename_subtitle_file(source_file_path, dest_file_path)
                break

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

def get_data_page(args, poolManager, url, data_session, search):
    clear()
    print('Searching...', end='\r')

    query = parse_search_query(search)

    url = f'{url}inc/ajax.php'

    payload = {
        'tabla': 'resultados',
        'filtros': '',
        f'buscar{data_session["web_version"]}': query,
        'token': data_session['token']
    }

    helper.logger.info(f'Starting request to subdivx.com with search: {search} parsed as: {query}')

    search_results = []

    response = https_request(poolManager, 'POST', url=url, fields=payload)

    try:
        data = json.loads(response.data).get('aaData')
    except JSONDecodeError:
        clear()
        print('Failed to parse response\nPlease try again')
        DataClient().delete_data()
        helper.logger.error('Failed to parse response, delete data session')
        exit(0)

    for result in data:
        subtitle = {
            'id_subtitle': result['id'],
            'title': filter_text(result['titulo']),
            'description': filter_text(result['descripcion']),
            'downloads': result['descargas'],
            'uploader': result['nick'],
            'upload_date': parse_date(result['fecha_subida']) if result['fecha_subida'] else '-'
        }
        search_results.append(subtitle)

    if not search_results:
        if not args.verbose:
            print('No subtitles found')
        helper.logger.info(f'No subtitles found for query: {query}')
        exit(0)

    helper.logger.info(f'Found subtitles for query: {query}')
    return search_results

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

def parse_date(date):
    try:
        return datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
    except ValueError:
        return None

def parse_user_input(input):
    search = input.strip()
    if search == '':
        print('Invalid search, try again')
        helper.logger.error('Invalid search')
        exit(0)
    return search

def parse_search_query(search):
    try:
        result = guessit(search)
        file_type = result['type']
        title = result['title']
        year = result.get('year', '')
        season = result.get('season', '')
        episode = result.get('episode', '')
    except KeyError:
        return search

    if file_type == 'episode':
        try:
            episode_number = f'E{episode:02d}' if episode else ''
            query = f'{title} S{season:02d}{episode_number}'
        except ValueError:
            return search
    else:
        query = f'{title} {year}'

    return query

def get_comments(poolManager, url, subtitle_id):
    payload = {
        'getComentarios': subtitle_id
    }

    url = f'{url}inc/ajax.php'

    try:
        response = poolManager.request('POST', url=url, fields=payload)
        comments_data = json.loads(response.data).get('aaData', [])
        helper.logger.info('Downloaded comments')
    except (ProtocolError, JSONDecodeError):
        helper.logger.error('Failed to parse response')
        return []

    comments = [filter_text(comment['comentario']) for comment in comments_data]

    return comments

def get_style_column_name(args):
    style = args.style or DEFAULT_STYLE

    if style == 'pretty':
        return 'Downloads'
    else:
        return 'Downloads'.ljust(11)

def print_search_results(args, search_data):
    terminal_width, _ = get_terminal_size()

    maxcolwidths = []

    # Check flag --minimal
    if args.minimal:
        columns = ['N°', 'Title', get_style_column_name(args), 'Date']
        align = ['center', 'center', 'decimal', 'center']
        min_width = 40

    elif args.alternative:
        columns = ['N°', 'Title', 'Description'.center(terminal_width // 2)]
        align = ['center', 'center', 'left']
        maxcolwidths = [None, terminal_width // 3,  terminal_width // 2]

    else:
        columns = ['N°', 'Title', get_style_column_name(args), 'Date', 'User']
        align = ['center', 'center', 'decimal', 'center', 'center']
        min_width = 55

    table_data = [columns]

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
        max_results = 4 if args.disable_help else 3
    elif args.compact:
        max_results = 3 if args.disable_help else 2

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
    time.sleep(0.5)

def filter_text(text):
    # Remove HTML tags from the text
    text = re.sub(r'<[^>]+>', '', text)

    # Replace multiple consecutive spaces with a single space
    text = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', text)

    # Replace &amp; with &
    text = text.replace('&amp;', '&')

    # Replace &quot; with "
    text = text.replace('&quot;', '"')

    return text

def print_description(args, selection, search_data):
    terminal_width, _ = get_terminal_size()
    description = search_data[selection]['description'].strip()

    description_table = [['Description'.center(terminal_width - 8)], [description]]

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
        summary.append([attribute.capitalize().replace('_', ' '), search_data[selection][attribute]])

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

def get_subtitle(args, poolManager, url, id_subtitle):
    if not args.verbose:
        print('Working...', end='\r')

    # Create temporal directory
    with tempfile.TemporaryDirectory() as temp_dir:
        helper.logger.info(f'Create temporal directory {temp_dir}')

        # Download zip/rar in temporal directory
        download_file(poolManager, url, id_subtitle, temp_dir)

        # Get file name and path
        file_name = os.listdir(temp_dir)[0]
        file_path = os.path.join(temp_dir, file_name)

        # Extract zip/rar
        if file_path.endswith('.zip'):
            unzip(file_path, temp_dir)
        elif file_path.endswith('.rar'):
            unrar(file_path, temp_dir)

        # Move all files from any subdirectories to the parent directory
        move_all_to_parent_directory(temp_dir)

        # Rename file extension if necessary
        rename_file_extension(temp_dir)

        # Get destination directory
        dest_dir = args.location or os.getcwd()

        # Rename and/or move subtitles
        rename_and_move_subtitle(args, temp_dir, dest_dir)

    # Message for user
    helper.logger.info(f'Delete temporal directory {temp_dir}')

    if not args.verbose:
        clear()
        print('Done!')

def normalize_key_values(key_values):
    source = key_values.get('source')
    if source:
        key_values['source'] = source.replace('Blu-ray', 'BluRay')

    video_codec = key_values.get('video_codec')
    if video_codec:
        key_values['video_codec'] = video_codec.replace('H.', '')

    size = key_values.get('size')
    if size:
        key_values['size'] = str(size)

    other = key_values.get('other')
    if other:
        key_values['other'] = ' '.join(other)

    return key_values

def get_best_match(args, search_data):
    helper.logger.info('Finding the best match subtitle')

    id_subtitle = search_data[0]['id_subtitle']
    id_secondary_subtitle = ''

    key_values = guessit(args.SEARCH)
    normalized_key_values = normalize_key_values(key_values)

    weights = get_attribute_weights()

    max_score = 0
    max_similarity_percentage = 0.8

    # Format the title based on the user input
    if key_values['type'] == 'episode':
        episode_number = f'E{key_values.get("episode"):02d}' if key_values.get('episode') is not None else ''
        title = f'{key_values.get("title")} S{key_values.get("season"):02d}{episode_number}'
        alt_title = f'{key_values.get("episode_title")}' if key_values.get('episode_title') else title
    else:
        title = f'{key_values.get("title")} ({key_values.get("year")})' if key_values.get('year') else key_values['title']
        alternative_title = key_values.get('alternative_title', '').replace('aka', '').strip()
        alt_title = (f'{alternative_title} ({key_values.get("year")})' if alternative_title else key_values.get('title')).strip()

    for subtitle in search_data:
        title_values = guessit(subtitle['title'])

        if key_values['type'] == 'episode':
            try:
                episode_number = f'E{title_values.get("episode"):02d}' if title_values.get('episode') is not None else ''
            except TypeError:
                episode_number_input = key_values.get('episode')
                episode_number_subtitle = title_values.get('episode')
                if episode_number_input is not None and episode_number_input in episode_number_subtitle:
                    episode_number = f'E{episode_number_input:02d}'
            title_filtered = f'{title_values.get("title")} S{title_values.get("season"):02d}{episode_number}'.replace(':', '').replace('.', '').strip()
            alt_title_filtered = f'{title_values.get("episode_title")}' if title_values.get('episode_title') else title_filtered
        else:
            title_filtered = f'{title_values.get("title")} ({title_values.get("year")})' if title_values.get('year') else title_values['title']
            alternative_title = title_values.get('alternative_title', '').replace('aka', '').strip()
            alt_title_filtered = (f'{alternative_title} ({title_values.get("year")})' if alternative_title else title_values.get('title')).strip()

        main_title_lower = title_filtered.lower()
        alt_title_lower = alt_title_filtered.lower()

        if (title.lower() == main_title_lower or
            title.lower() == alt_title_lower or
            alt_title.lower() == main_title_lower or
            alt_title.lower() == alt_title_lower):
            id_secondary_subtitle = subtitle['id_subtitle']

            score = 0

            # Search for match in description
            for key in weights.keys():
                try:
                    subtitle_description = subtitle['description'].replace('Blu-Ray', 'BluRay').lower()

                    # If the edition is found in the subtitle description, consider it as the best match
                    if key_values.get('edition') and key_values['edition'].lower() in subtitle_description:
                        id_subtitle = subtitle['id_subtitle']

                    attribute = normalized_key_values[key].lower()

                    if attribute in subtitle_description:
                        score += weights[key]
                        helper.logger.info(f'Found attribute [{key}] in subtitle [{subtitle["id_subtitle"]}]')
                except KeyError:
                    pass

            if max_score < score:
                max_score = score
                id_subtitle = subtitle['id_subtitle']
                helper.logger.info(f'New best match with score {max_score:.2f} is subtitle [{id_subtitle}]')

        if max_score >= max_similarity_percentage:
            break

    if max_score > 0:
        helper.logger.info(f'Returning the best match for {args.SEARCH} is subtitle [{id_subtitle}] with score {max_score:.2f}')
        return id_subtitle
    elif id_secondary_subtitle:
        helper.logger.info('Returning the first subtitle found with matching with title')
        return id_secondary_subtitle
    else:
        helper.logger.info('Returning the first subtitle found')
        return id_subtitle

def print_comments(args, comments):
    terminal_width, _ = get_terminal_size()

    table = [['N°', 'Comment'.center(terminal_width - 15)]]
    for index, comment_text in enumerate(comments, start=1):
        table.append([index, comment_text.strip()])

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
        'total_pages': total_pages}
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
        page_info_format = f'[{current_page}/{total_pages}]'
        terminal_width, _ = get_terminal_size()
        print(page_info_format.center(terminal_width))

        if total_pages > 1:
            user_input = prompt_user_selection(args, 'comments')
        else:
            user_input = prompt_user_selection(args, 'download')

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

    main_menu = '[1-9] Select [ 0 ] Exit'.center(terminal_width)
    secondary_menu = '[ 1 ] Download [ 0 ] Exit'.center(terminal_width)
    paginate_menu = '[ n ] Next page [ p ] Previous page'.center(terminal_width)

    menu_options = {
        'subtitle': main_menu,
        'pagination': main_menu + '\n' + paginate_menu,
        'download': secondary_menu,
        'comments': secondary_menu + '\n' + paginate_menu
    }[menu_name]

    if not args.disable_help:
        print('\n' + menu_options.center(terminal_width))

    try:
        user_input = input('\n' + padding + 'Selection: ')
    except (KeyboardInterrupt, EOFError):
        exit(1)

    return user_input

def get_random_revision():
    return f'13{random.randrange(8)}.0' # 130.0 - 137.0

def https_request(https, method, url, **kwargs):
    try:
        response = https.request(method, url, **kwargs)
        if 400 <= response.status < 600 and 'www.subdivx.com/sub' not in url:
            raise Exception(f'HTTP Error: {response.status}')
    except TimeoutError:
        print('Timeout error, check your internet connection')
        helper.logger.error('Timeout error')
        exit(1)
    except MaxRetryError:
        print('Connection error, check your internet connection')
        helper.logger.error('Connection error')
        exit(1)
    except Exception as e:
        print(f'An Error occurred: {e}')
        helper.logger.error(f'{e}')
        exit(1)

    return response

# -- Class Cookie -- #
class Cookie:
    def __init__(self, poolManager, url):
        self.poolManager = poolManager
        self.url = url

    def get_cookie(self):
        response = https_request(self.poolManager, 'GET', self.url)

        cookie = response.headers.get('Set-Cookie')
        cookie_parts = cookie.split(';')

        return cookie_parts[0] # sdx_cookie

# -- Class Token -- #
class Token:
    _TIMEDELTA = timedelta(hours=1)

    def __init__(self, poolManager, url, cookie):
        self.poolManager = poolManager
        self.url = url
        self.cookie = cookie
        self._generate_token()

    def _generate_token(self):
        self.poolManager.headers['cookie'] = self.cookie

        response = https_request(self.poolManager, 'GET', f'{self.url}inc/gt.php?gt=1')
        data = response.data

        self._TOKEN_VALUE = json.loads(data)['token']
        self._expiration_date = datetime.now() + self._TIMEDELTA

    def get_token_data(self):
        data = {
            'token': self._TOKEN_VALUE,
            'expiration_date': self._expiration_date.isoformat().replace('+00:00', '')
        }

        return data

# -- Class DataClient -- #
class DataClient():
    _PATH_DATA = os.path.join(tempfile.gettempdir(), 'sdx-dl.json')

    def __init__(self, poolManager=None, header=None, url=None):
        self.poolManager = poolManager
        self.header = header
        self.url = url

    def _get_web_version(self, poolManager, url):
        response = https_request(poolManager, 'GET', url)
        response_data = response.data.decode('utf-8')

        label = 'id="vs">'

        version_start_index = response_data.find(label) + len(label)
        version_end_index = response_data.find('</div>', version_start_index)

        version_text = response_data[version_start_index:version_end_index]

        version = version_text.replace('v', '').replace('.', '')

        return version

    def generate_data(self):
        print('Generating data session...', end='\r')
        helper.logger.info('Generate data session')
        self.web_version = self._get_web_version(self.poolManager, self.url)
        self.sdx_cookie = Cookie(self.poolManager, self.url).get_cookie()
        self.token_data = Token(self.poolManager, self.url, self.sdx_cookie).get_token_data()

    def save_data(self):
        data = {
            'web_version': self.web_version,
            'sdx_cookie': self.sdx_cookie,
            'token': self.token_data['token'],
            'expiration_date': self.token_data['expiration_date']
        }

        with open(self._PATH_DATA, 'w') as file:
            json.dump(data, file, indent=4)
            file.close()

    def _read_data(self):
        with open(self._PATH_DATA, 'r') as file:
            self._data = json.load(file)
            file.close()

    def get_data_session(self):
        if self.does_data_exist():
            helper.logger.info('Load data session')
            self._read_data()
            self.header['cookie'] = self._data['sdx_cookie'] # Set cookie in header
            return self._data

    def delete_data(self):
        if self.does_data_exist():
            os.remove(self._PATH_DATA)

    def does_data_exist(self):
        return os.path.exists(self._PATH_DATA)

    def does_data_session_expire(self):
        if self.does_data_exist():
            self._read_data()

            expiration_date = datetime.fromisoformat(self._data['expiration_date'])

            if datetime.now() > expiration_date:
                return True

            return False

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

    def SEARCH(self):
        return self.SEARCH

    def comment(self):
        return self.comment

    def first(self):
        return self.first

    def lines(self):
        return self.lines

    def location(self):
        return self.location

    def minimal(self):
        return self.minimal

    def alternative(self):
        return self.alternative

    def compact(self):
        return self.compact

    def no_rename(self):
        return self.no_rename

    def no_exit(self):
        return self.no_exit

    def order_by_downloads(self):
        return self.order_by_downloads

    def order_by_dates(self):
        return self.order_by_dates

    def save_config(self):
        return self.save_config

    def season(self):
        return self.season

    def style(self):
        return self.style

    def load_config(self):
        return self.load_config

    def disable_help(self):
        return self.disable_help

    def verbose(self):
        return self.verbose

# -- Class Config -- #
class Config():
    _CONFIG_FILE_NAME = 'config.json'

    def __init__(self):
        self.config_directory = self._create_config_directory()
        self.config_path = os.path.join(self.config_directory, self._CONFIG_FILE_NAME)

    def _create_config_directory(self):
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

        args_to_delete = ['SEARCH', 'load_config', 'save_config']

        for arg in args_to_delete:
            args_copy.pop(arg, None)

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
# Get from https://medium.com/@denis.volokh/caching-methods-implementations-and-comparisons-in-python-7d29a2b0cd80

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
