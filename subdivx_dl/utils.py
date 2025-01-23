# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import re
import json
import time
import shutil
import datetime
import tempfile
import textwrap
import platform

from json import JSONDecodeError
from urllib3.exceptions import ProtocolError
from tempfile import NamedTemporaryFile
from tabulate import tabulate, SEPARATING_LINE
from zipfile import ZipFile
from rarfile import RarFile
from guessit import guessit
from subdivx_dl import helper

SUBTITLE_EXTENSIONS = ('.srt', '.SRT', '.sub', '.ass', '.ssa', 'idx')

DEFAULT_STYLE = 'pretty'

def get_terminal_width():
    try:
        terminal_size = shutil.get_terminal_size()
        return terminal_size.columns
    except OSError:
        return 80

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

        return '.bin'

def download_file(poolManager, url, id_subtitle, location):
    helper.logger.info(f'Downloading archive from: {url}{id_subtitle} in {location}')

    success = False

    with NamedTemporaryFile(dir=location, delete=False) as temp_file:
        for i in range(9, 0, -1):
            server_address = f'{url}sub{i}/{id_subtitle}'
            helper.logger.info(f'Attempt on server N°{i} with url {server_address}')

            response = poolManager.request('GET', server_address)
            temp_file.write(response.data)
            temp_file.seek(0)

            file_extension = get_file_extension(temp_file.name)

            if file_extension in ('.zip', '.rar'):
                helper.logger.info('Download complete')

                new_file_path = temp_file.name + file_extension
                temp_file.close()
                os.rename(temp_file.name, new_file_path)

                success = True
                break
            else:
                success = False

        if not success:
            print(f'No subtitles were downloaded because the link is broken')
            helper.logger.error(f'Subtitles not downloaded, link broken: {url}{id_subtitle}')
            exit(1)

def unzip(zip_file_path, destination):
    try:
        with ZipFile(zip_file_path, 'r') as z:
            helper.logger.info(f'Unpacking zip [{os.path.basename(z.filename)}]')
            for file in z.namelist():
                if file.endswith(SUBTITLE_EXTENSIONS):
                    helper.logger.info(f'Unzip [{os.path.basename(file)}]')
                    z.extract(file, destination)
            z.close()
    except:
        helper.logger.error('File corrupt')
        print('Invalid file')
        exit(1)
    else:
        move_all_to_parent_folder(destination)

def move_all_to_parent_folder(directory):
    for (root, dirs, files) in os.walk(directory, topdown=True):
        for d in dirs:
            if d != '__MACOSX':
                subfolder = os.path.join(directory, dirs[0])
                for (root, dirs, files) in os.walk(subfolder, topdown=True):
                    for name in files:
                        source_path = os.path.join(root, name)
                        destination_path = os.path.join(directory, name)
                        shutil.copy(source_path, destination_path)

def unrar(rar_file_path, destination):
    helper.logger.info(f'Unpacking rar [{os.path.basename(rar_file_path)}] in {destination}')
    rf = RarFile(rar_file_path)

    for file in rf.namelist():
        if file.endswith(SUBTITLE_EXTENSIONS):
            helper.logger.info(f'Unrar [{os.path.basename(file)}]')
            rf.extract(file, destination)
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
                atribute = normalized_key_values[key].lower()

                if atribute in subtitle_name:
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
    files = os.listdir(directory)

    data = []

    index = 1
    x = 0
    while x < len(files):
        if files[x].endswith(SUBTITLE_EXTENSIONS):
            data.append(index)
            data.append(os.path.basename(files[x]))
            header.append(data[:])
            data.clear()
            index += 1
        x += 1

    if args.fast and index > 2:
        file_name = select_best_subtitle_from_list(args, header)
        return file_name

    if index > 2:
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
            user_input = prompt_user_selection('download')

            try:
                selection = int(user_input) - 1
                file_name = header[selection + 1][1]
            except (ValueError, IndexError):
                print('\nInput valid numbers')
                delay(0)
                continue

            if selection < -1:
                print('\nInput only positive numbers')
                delay(0)
                continue
            elif selection == -1:
                # Remove temp folder
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
        # Return the file_name of the subtitle, excluding .zip or .rar extensions
        for x in range(2):
            if files[x].endswith(SUBTITLE_EXTENSIONS):
                return os.path.basename(files[x])

def movie_subtitle(args, file_path, destination):
    helper.logger.info(f'Move subtitle to {destination}')

    file_name_select = print_menu_content_dir(args, file_path)
    file_path_select = os.path.join(file_path, file_name_select)

    # Rename file
    search_name, file_extension = os.path.splitext(args.SEARCH)
    new_name = search_name.strip()

    # Get file extension of subtitle downloaded
    subtitle_file_extension = os.path.splitext(file_path_select)[1]

    origin_name = os.path.basename(file_path_select)

    if not args.no_rename:
        new_name = os.path.join(destination, f'{new_name}{subtitle_file_extension}')

        destination_name = os.path.basename(new_name)
        helper.logger.info(f'Rename and move subtitle [{origin_name}] to [{destination_name}]')

        destination_path = os.path.dirname(new_name)
        os.makedirs(destination_path, exist_ok=True)

        try:
            shutil.copy(file_path_select, new_name)
        except PermissionError:
            if not args.verbose:
                clear()
                print(f'You do not have permissions to write to {destination_path}')
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

    else:
        new_name = os.path.join(destination, origin_name)
        helper.logger.info(f'Just move subtitle [{origin_name}] to [{destination}]')

        destination_path = os.path.dirname(new_name)
        os.makedirs(destination_path, exist_ok=True)

        try:
            shutil.copy(file_path_select, new_name)
        except PermissionError:
            if not args.verbose:
                clear()
                print(f'You do not have permissions to write to {destination_path}')
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

def tv_show_subtitles(args, file_path, destination):
    helper.logger.info(f'Moves subtitles to {destination}')
    files = os.listdir(file_path)

    # TV series season and episode names
    patternSeriesTv = r'(.*?)[.\ssS](\d{1,2})[eExX](\d{1,3}).*'

    index = 0

    while index < len(files):
        file_origin = os.path.join(file_path, files[index])
        subtitle_file_extension = os.path.splitext(files[index])[1]

        if files[index].endswith(SUBTITLE_EXTENSIONS) and not args.no_rename:
            result = re.search(patternSeriesTv, files[index])

            try:
                get_tv_show = result.group(1)
                get_season = result.group(2)
                get_episode = result.group(3)

                serie = get_tv_show
                season = f'S{get_season}'
                episode = f'E{get_episode}'

                exclude = ['.', '-']
                for i in exclude:
                    serie = serie.replace(i, ' ')

                # Remove double spaces and end space in name tv show
                serie = serie.replace('  ', '').rstrip()

                # Format name example:
                # Serie - S05E01.srt | S05E01.srt
                if serie != '':
                    new_name = f'{serie} - {season}{episode}{subtitle_file_extension}'
                else:
                    new_name = f'{season}{episode}{subtitle_file_extension}'

            except Exception as e:
                helper.logger.error(e)
                file_destination = os.path.join(destination, files[index])
                helper.logger.info(f'No match Regex: Just move subtitle [{files[index]}]')

                os.makedirs(os.path.dirname(file_destination), exist_ok=True)

                try:
                    shutil.copy(file_origin, file_destination)
                except PermissionError:
                    if not args.verbose:
                        clear()
                        print(f'Permission denied for writing to {os.path.dirname(file_destination)}')
                    helper.logger.warning('Permissions issues on destination directory')
                    exit(0)
            else:
                file_destination = os.path.join(destination, new_name)
                helper.logger.info(f'Move subtitle [{files[index]}] as [{new_name}]')

                os.makedirs(os.path.dirname(file_destination), exist_ok=True)

                try:
                    shutil.copy(file_origin, file_destination)
                except PermissionError:
                    if not args.verbose:
                        clear()
                        print(f'You do not have permissions to write here {os.path.dirname(file_destination)}')
                    helper.logger.warning('Permissions issues on destination directory')
                    exit(0)

        # Move (rename same name for override) files without rename if flag --no-rename is True
        elif files[index].endswith(SUBTITLE_EXTENSIONS):
            file_destination = os.path.join(destination, files[index])
            helper.logger.info(f'Move subtitle [{files[index]}] to [{destination}]')

            os.makedirs(os.path.dirname(file_destination), exist_ok=True)

            try:
                shutil.copy(file_origin, file_destination)
            except PermissionError:
                if not args.verbose:
                    clear()
                    print(f'You do not have permissions to write here {os.path.dirname(file_destination)}')
                helper.logger.warning('Permissions issues on destination directory')
                exit(0)
        index += 1

def rename_and_move_subtitle(args, file_path, destination):
    # Check flag --season
    if not args.season:
        # Rename single srt
        movie_subtitle(args, file_path, destination)
    else:
        # Move and rename bulk srt
        tv_show_subtitles(args, file_path, destination)

def get_data_page(args, poolManager, url, token, search):
    print('Searching...', end='\r')

    query = parse_search_query(search)
    version = get_web_version(poolManager, url)

    url = f'{url}inc/ajax.php'

    payload = {
        'tabla': 'resultados',
        'filtros': '',
        f'buscar{version}': query,
        'token': token
    }

    helper.logger.info(f'Starting request to subdivx.com with search: {search} parsed as: {query}')

    max_attempts = 3
    search_results = []

    for attempt in range(max_attempts):
        helper.logger.info(f'Attempt number {attempt + 1}')

        if attempt > 0:
            delay()

        response = poolManager.request('POST', url=url, fields=payload)

        try:
            data = json.loads(response.data).get('aaData')
        except JSONDecodeError:
            clear()
            print('Subtitles not found because cookie expired')
            delete_cookie()
            print('\nCookie deleted')
            print('\nTry again')

            helper.logger.error('Failed to parse response')
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

        if not search_results and attempt < (max_attempts - 1):
            continue
        elif search_results:
            helper.logger.info(f'Subtitles found for: {query}')
            break
        elif not search_results and attempt == max_attempts - 1:
            helper.logger.info(f'Subtitles not found for: {query}')
            if not args.verbose:
                print('Subtitles not found')
            exit(0)

    return search_results

def sort_data(args, data):
    if args.order_by_downloads:
        return sorted(data, key=lambda item: item['downloads'], reverse=True)
    elif args.order_by_dates:
        sorted_data = sorted(
            data,
            key=lambda item: (
                datetime.datetime.strptime(item['upload_date'], '%d/%m/%Y'
                if item['upload_date'] != '-' else '-')
            ),
            reverse = True
        )
        return sorted_data

def parse_date(date):
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
    except ValueError:
        return None

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

    comments = [comment['comentario'] for comment in comments_data]

    return comments

def get_style_column_name(args):
    style = args.style or DEFAULT_STYLE

    if style == 'pretty':
        return 'Downloads'
    else:
        return 'Downloads'.ljust(11)

def print_search_results(args, search_data):
    terminal_width = get_terminal_width()

    maxcolwidths = []

    # Check flag --minimal
    if args.minimal:
        columns = ['N°', 'Title', get_style_column_name(args), 'Date']
        align = ['center', 'center', 'decimal', 'center']
        min_width = 40

    elif args.alternative:
        columns = ['N°', 'Title', 'Description'.center(terminal_width // 2)]
        align = ['center', 'center', 'left']
        maxcolwidths = [None, (terminal_width // 3) + 5,  terminal_width // 2]

    else:
        columns = ['N°', 'Title', get_style_column_name(args), 'Date', 'User']
        align = ['center', 'center', 'decimal', 'center', 'center']
        min_width = 50

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

def print_search_results_compact(args, search_data):
    terminal_width = get_terminal_width()

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
    terminal_width = get_terminal_width()

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

def filter_text(text):
    # Remove HTML tags from the text
    text = re.sub(r'<[^>]+>', '', text)

    # Replace multiple consecutive spaces with a single space
    text = re.sub(r'(?<=\S) {2,}(?=\S)', ' ', text)

    # Replace &amp; with &
    text = text.replace('&amp;', '&')

    return text

def print_description(args, selection, search_data):
    terminal_width = get_terminal_width()
    description = search_data[selection]['description'].strip()

    description_table = [['Description'.center(terminal_width - 8)], [description]]

    print_centered(
        args,
        tabulate(
            description_table,
            headers='firstrow',
            tablefmt=args.style or DEFAULT_STYLE,
            stralign='left',
            maxcolwidths=[terminal_width - 5]
        ), end='\n\n'
    )

def print_summary(args, selection, search_data):
    terminal_width = get_terminal_width()

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
        ), end='\n\n'
    )

def get_subtitle(args, poolManager, url, id_subtitle):
    if not args.verbose:
        print('Working...', end='\r')

    # Check flag --location
    LOCATION_DESTINATION = args.location

    # Create temporal directory
    temp_dir = tempfile.TemporaryDirectory()
    fpath = temp_dir.name
    helper.logger.info(f'Create temporal directory {fpath}')

    # Download zip/rar in temporal directory
    download_file(poolManager, url, id_subtitle, fpath)

    # Determinate final path for subtitle
    if LOCATION_DESTINATION is None:
        parent_folder = os.getcwd()
    else:
        parent_folder = LOCATION_DESTINATION

    # In case the server does not return a file, exit
    list_directory = os.listdir(fpath)

    if not list_directory:
        helper.logger.info('Remote server not found file')

        helper.logger.info(f'Delete temporal directory {fpath}')
        temp_dir.cleanup()

        if not args.verbose:
            clear()
            print('Subtitle not found because server missing file')
        exit(0)

    # Extract zip/rar file
    for file in list_directory:
        file_path = os.path.join(fpath, file)

        if file.endswith('.zip'):
            unzip(file_path, fpath)
        elif file.endswith('.rar'):
            unrar(file_path, fpath)

    # Rename and/or move subtitles
    rename_and_move_subtitle(args, fpath, parent_folder)

    # Remove temp folder
    try:
        temp_dir.cleanup()
        helper.logger.info(f'Delete temporal directory {fpath}')
    except OSError as error:
        helper.logger.error(error)

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
        key_values['other'] = ''.join(other)

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

    for subtitle in search_data:

        # Search for match in title
        if key_values['type'] == 'episode':
            episode_number = f'E{key_values.get("episode"):02d}' if key_values.get('episode') is not None else ''
            title = f'{key_values.get("title")} S{key_values.get("season"):02d}{episode_number}'
        else:
            title = f'{key_values.get("title")} ({key_values.get("year")})' if key_values.get('year') else key_values['title']

        # Search for match in title of subtitle
        if title.lower() in subtitle['title'].lower() or key_values['title'].lower() in subtitle['title'].lower():
            id_secondary_subtitle = subtitle['id_subtitle']

            score = 0

            # Search for match in description
            for key in weights.keys():
                try:
                    subtitle_description = subtitle['description'].replace('Blu-Ray', 'BluRay').lower()
                    atribute = normalized_key_values[key].lower()

                    if atribute in subtitle_description:
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
    terminal_width = get_terminal_width()

    table = [['N°', 'Comment'.center(terminal_width - 20)]]
    for index, comment_text in enumerate(comments, start=1):
        table.append([index, comment_text.strip()])

    tablefmt = args.style or DEFAULT_STYLE
    colalign = ['center', 'left']
    maxcolwidths = [None, terminal_width - 12]

    print_centered(
        args,
        tabulate(
            table, headers='firstrow', tablefmt=tablefmt, colalign=colalign, maxcolwidths=maxcolwidths
        )
    )

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def prompt_user_selection(args, menu_name: str, options: list = ['subtitle', 'download', 'pagination']):
    terminal_width = get_terminal_width()
    padding = ' ' * ((terminal_width // 2) - 6)

    basic_menu = '[1-9] Select [ 0 ] Exit'.center(terminal_width)

    menu_options = {
        'download': '[ 1 ] Download [ 0 ] Exit',
        'subtitle': basic_menu,
        'pagination': basic_menu + '[ n ] Next page [ p ] Previous page'.center(terminal_width),
    }[menu_name]

    if not args.disable_help:
        print('\n' + menu_options.center(terminal_width))

    try:
        user_input = input('\n' + padding + 'Selection: ')
    except (KeyboardInterrupt, EOFError):
        exit(1)

    return user_input

def get_web_version(poolManager, url):

    response = poolManager.request('GET', url)
    response_data = response.data.decode('utf-8')

    label = 'id="vs">'

    version_start_index = response_data.find(label) + len(label)
    version_end_index = response_data.find('</div>', version_start_index)

    version_text = response_data[version_start_index:version_end_index]

    version = version_text.replace('v', '').replace('.', '')

    return version

def delay(factor=2):
    delay = 2 ** factor
    time.sleep(delay)

##############################################################################
# Cookie functions
##############################################################################

COOKIE_NAME = 'sdx-dl'

def exist_cookie():
    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, COOKIE_NAME)

    return os.path.exists(cookie_path)

def read_cookie():
    helper.logger.info('Read cookie')

    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, COOKIE_NAME)

    with open(cookie_path, 'r') as file:
        return file.read()

def get_cookie(poolManager, url):
    helper.logger.info(f'Get cookie from {url}')

    response = poolManager.request('GET', url)

    cookie = response.headers.get('Set-Cookie')
    cookie_parts = cookie.split(';')

    # Return sdx_cookie
    return cookie_parts[0]

def save_cookie(sdx_cookie):
    # Save cookie in temporary folder
    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, COOKIE_NAME)

    with open(cookie_path, 'w') as file:
        file.write(sdx_cookie)
        file.close()

    helper.logger.info('Save cookie')

def set_cookie(poolManager, url, header):
    cookie = None

    if not exist_cookie():
        cookie = get_cookie(poolManager, url)
        save_cookie(cookie)
    else:
        cookie = read_cookie()

    header['cookie'] = cookie

def delete_cookie():
    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, COOKIE_NAME)

    if os.path.exists(cookie_path):
        os.remove(cookie_path)

def get_token(poolManager, url):
    helper.logger.info('Get token')

    url = f'{url}inc/gt.php?gt=1'

    response = poolManager.request('GET', url)
    data = response.data

    token = json.loads(data)['token']

    return token

##############################################################################
# Class Args
##############################################################################

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

##############################################################################
# Configuration functions
##############################################################################

CONFIG_FILE_NAME = 'config.json'

def create_config_directory():
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

def save_config(args):
    config_directory = create_config_directory()
    config_path = os.path.join(config_directory, CONFIG_FILE_NAME)

    args_copy = args.__dict__.copy()

    args_to_delete = ['SEARCH', 'load_config', 'save_config']

    for arg in args_to_delete:
        args_copy.pop(arg, None)

    with open(config_path, 'w') as file:
        json.dump(args_copy, file, indent=4, sort_keys=True)

    helper.logger.info(f'Save configuration file {config_path}')

def load_config():
    config_path = os.path.join(create_config_directory(), CONFIG_FILE_NAME)

    if not os.path.exists(config_path):
        helper.logger.info('Not found configuration file, usage default values')
        return {}

    with open(config_path, 'r') as file:
        helper.logger.info(f'Load configuration file {config_path}')
        return json.load(file)

##############################################################################
# Class TTLCache
##############################################################################

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