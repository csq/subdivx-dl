# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import tempfile
import textwrap
import datetime
import shutil
import json
import time
import os
import re

from tempfile import NamedTemporaryFile
from json import JSONDecodeError
from tabulate import tabulate
from subdivx_dl import helper
from rarfile import RarFile
from zipfile import ZipFile
from guessit import guessit

subtitle_extensions = ('.srt', '.SRT', '.sub', '.ass', '.ssa', 'idx')

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

def download_file(poolManager, url, location):
    helper.logger.info('Downloading archive from: %s in %s', url, location)

    success = False

    with NamedTemporaryFile(dir=location, delete=False) as temp_file:
        for i in range(9, 0, -1):
            address = url[:20] + 'sub' + str(i) + '/' + url[20:]
            helper.logger.info('Attempt on server N°%d with url %s', i, address)

            response = poolManager.request('GET', address, preload_content=False)
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
            print(f'No suitable subtitles download for: {url}')

def unzip(zip_file_path, destination):
    try:
        with ZipFile(zip_file_path, 'r') as z:
            helper.logger.info('Unpacking zip [%s]', os.path.basename(z.filename))
            for file in z.namelist():
                if file.endswith(subtitle_extensions):
                    helper.logger.info('Unzip [%s]', os.path.basename(file))
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
                        shutil.copy(os.path.join(root, name), os.path.join(directory, name))

def unrar(rar_file_path, destination):
    helper.logger.info('Unpacking rar [%s] in %s', os.path.basename(rar_file_path), destination)
    rf = RarFile(rar_file_path)

    for file in rf.namelist():
        if file.endswith(subtitle_extensions):
            helper.logger.info('Unrar [%s]', os.path.basename(file))
            rf.extract(file, destination)
    rf.close()

def print_menu_content_dir(args, directory):
    header = [['N°', 'File name']]
    files = os.listdir(directory)

    data = []

    index = 1
    x = 0
    while x < len(files):
        if files[x].endswith(subtitle_extensions):
            data.append(index)
            data.append(os.path.basename(files[x]))
            header.append(data[:])
            data.clear()
            index += 1
        x += 1

    if index > 2:
        while True:
            # Clear screen
            clear()

            # Print table with of the subtitles available
            if not args.grid:
                print(tabulate(header, headers='firstrow', tablefmt='pretty', stralign='left'))
            else:
                print(tabulate(header, headers='firstrow', tablefmt='fancy_grid', stralign='left'))

            user_input = select_menu()

            try:
                selection = int(user_input) - 1
                file_name = header[selection + 1][1]
            except ValueError:
                print('\nInput only numbers')
                delay(0)
                continue
            except IndexError:
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
                    helper.logger.info('Delete temporal directory %s', directory)
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
            if files[x].endswith(subtitle_extensions):
                return os.path.basename(files[x])

def movie_subtitle(args, file_path, destination):
    helper.logger.info('Move subtitle to %s', destination)

    file_name_select = print_menu_content_dir(args, file_path)
    file_path_select = os.path.join(file_path, file_name_select)

    # Rename file
    search_name, file_extension = os.path.splitext(args.SEARCH)
    new_name = search_name.strip()

    # Get file extension of subtitle downloaded
    subtitle_file_extension = os.path.splitext(file_path_select)[1]

    if not args.no_rename:
        new_name = os.path.join(destination, f'{new_name}{subtitle_file_extension}')
        helper.logger.info(
            'Rename and move subtitle [%s] to [%s]',
            os.path.basename(file_path_select),
            os.path.basename(new_name)
        )

        os.makedirs(os.path.dirname(new_name), exist_ok=True)

        try:
            shutil.copy(file_path_select, new_name)
        except PermissionError:
            if not args.verbose:
                clear()
                print(f'You do not have permissions to write to {os.path.dirname(new_name)}')
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

    else:
        new_name = os.path.join(destination, os.path.basename(file_path_select))
        helper.logger.info('Just move subtitle [%s] to [%s]', os.path.basename(file_path_select), destination)

        os.makedirs(os.path.dirname(new_name), exist_ok=True)

        try:
            shutil.copy(file_path_select, new_name)
        except PermissionError:
            if not args.verbose:
                clear()
                print(f'You do not have permissions to write to {os.path.dirname(new_name)}')
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

def tv_show_subtitles(args, file_path, destination):
    helper.logger.info('Moves subtitles to %s', destination)
    files = os.listdir(file_path)

    # TV series season and episode names
    patternSeriesTv = r'(.*?)[.\ssS](\d{1,2})[eExX](\d{1,3}).*'

    index = 0

    while index < len(files):
        file_origin = os.path.join(file_path, files[index])
        subtitle_file_extension = os.path.splitext(files[index])[1]

        if files[index].endswith(subtitle_extensions) and not args.no_rename:
            result = re.search(patternSeriesTv, files[index])

            try:
                get_tv_show = result.group(1)
                get_season = result.group(2)
                get_episode = result.group(3)

                serie = get_tv_show
                season = 'S' + get_season
                episode = 'E' + get_episode

                exclude = ['.', '-']
                for i in exclude:
                    serie = serie.replace(i, ' ')

                # Remove double spaces and end space in name tv show
                serie = serie.replace('  ', '').rstrip()

                # Format name example:
                # Serie - S05E01.srt | S05E01.srt
                if serie != '':
                    new_name = serie + ' - ' + season + episode + subtitle_file_extension
                else:
                    new_name = season + episode + subtitle_file_extension

            except Exception as e:
                helper.logger.error(e)
                file_destination = os.path.join(destination, files[index])
                helper.logger.info('No match Regex: Just move subtitle [%s]', files[index])

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
                helper.logger.info('Move subtitle [%s] as [%s]', files[index], new_name)

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
        elif files[index].endswith(subtitle_extensions):
            file_destination = os.path.join(destination, files[index])
            helper.logger.info('Move subtitle [%s] to [%s]',  files[index], destination)

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
    version = get_web_version(poolManager)

    payload = {
        'tabla': 'resultados',
        'filtros': '',
        f'buscar{version}': query,
        'token': token
    }

    helper.logger.info('Starting request to subdivx.com with search: %s parsed as: %s', search, query)

    max_attempts = 3
    search_results = []

    for attempt in range(max_attempts):
        helper.logger.info('Attempt number %s', attempt + 1)

        if attempt > 0:
            delay()

        request = poolManager.request('POST', url=url, fields=payload)

        try:
            data = json.loads(request.data).get('aaData')
        except JSONDecodeError:
            clear()
            print('Subtitles not found because cookie expired')
            delete_cookie()
            print('\nCookie deleted')
            print('\nTry again')

            helper.logger.error('Response could not be serialized')
            exit(0)

        for result in data:
            subtitle = {
                'id_subtitle': result['id'],
                'title': result['titulo'],
                'description': result['descripcion'],
                'downloads': result['descargas'],
                'uploader': result['nick'],
                'upload_date': parse_date(result['fecha_subida']) if result['fecha_subida'] else '-'
            }
            search_results.append(subtitle)

        if not search_results and attempt < (max_attempts - 1):
            continue
        elif search_results:
            helper.logger.info('Subtitles found for: %s', query)
            break
        elif not search_results and attempt == max_attempts - 1:
            helper.logger.info('Subtitles not found for: %s', query)
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

def get_comments(poolManager, url, id_subtitle):

    payload = {
        'getComentarios': id_subtitle
    }

    request = poolManager.request('POST', url, fields=payload)

    try:
        data = json.loads(request.data).get('aaData')
    except JSONDecodeError:
        print('Comments not found')
        helper.logger.error('Response could not be serialized')
        exit(0)

    comment_list = []

    for key in data:
        comment_list.append(key['comentario'])

    return comment_list

def print_search_result(args, search_data):
    # Get terminal width
    terminal_width = get_terminal_width()

    # Initialize header
    data = [['N°', 'Title', 'Downloads', 'Date', 'User']]

    # Iterate over search results
    for index, item in enumerate(search_data, start=1):

        # Shorten title if necessary
        if args.grid:
            title = textwrap.shorten(item['title'], width=terminal_width - 40, placeholder='...')
        else:
            title = textwrap.shorten(item['title'], width=terminal_width - 55, placeholder='...')

        # Create row for table
        row = [index, title, item['downloads'], item['upload_date'], item['uploader']]

        # Append row to data
        data.append(row)

    # Print table
    if args.grid:
        print(tabulate(
            data,
            headers='firstrow',
            tablefmt='fancy_grid',
            colalign=('center', 'center', 'decimal', 'center', 'center')
        ))
    else:
        print(tabulate(
            data,
            headers='firstrow',
            tablefmt='pretty',
            colalign=('center', 'center', 'decimal')
        ))

def print_select_description(args, selection, search_data):
    # Get terminal width
    terminal_width = get_terminal_width()

    # Initialize header
    description_select = [['Description']]

    # Get description
    description = search_data[selection]['description'].strip()
    description_select.append([description])

    # Print table
    if args.grid:
        print(tabulate(
            description_select,
            headers='firstrow',
            tablefmt='fancy_grid',
            stralign='left',
            maxcolwidths=[terminal_width - 5]
        ))
    else:
        print(tabulate(
            description_select,
            headers='firstrow',
            tablefmt='pretty',
            stralign='left',
            maxcolwidths=[terminal_width - 5]
        ))

def get_subtitle(args, poolManager, url):
    if not args.verbose:
        print('Working...', end='\r')

    # Check flag --location
    LOCATION_DESTINATION = args.location

    # Create temporal directory
    temp_dir = tempfile.TemporaryDirectory()
    fpath = temp_dir.name
    helper.logger.info('Create temporal directory %s', fpath)

    # Download zip/rar in temporal directory
    download_file(poolManager, url, fpath)

    # Determinate final path for subtitle
    if LOCATION_DESTINATION is None:
        parent_folder = os.getcwd()
    else:
        parent_folder = LOCATION_DESTINATION

    # In case the server does not return a file, exit
    list_directory = os.listdir(fpath)

    if not list_directory:
        helper.logger.info('Remote server not found file')

        helper.logger.info('Delete temporal directory %s', fpath)
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
        helper.logger.info('Delete temporal directory %s', fpath)
    except OSError as error:
        helper.logger.error(error)

    if not args.verbose:
        clear()
        print('Done')

def print_select_comments(args, comment_list):
    # Get terminal width
    terminal_width = get_terminal_width()

    # Initialize header
    header = ['N°', 'Comments']
    comment = []

    # Iterate over comments
    for index, text in enumerate(comment_list, start=1):
        comment.append([index, text.strip()])

    # Print table
    if args.grid:
        print(tabulate(
            comment,
            headers=header,
            tablefmt='fancy_grid',
            colalign=('center', 'left'),
            maxcolwidths=[None, terminal_width - 12]
        ))
    else:
        print(tabulate(
            comment,
            headers=header,
            tablefmt='pretty',
            colalign=('center', 'left'),
            maxcolwidths=[None, terminal_width - 10]
        ))

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    print('\n[1~9] Select')
    print('[ 0 ] Exit\n')

    user_input = input('Selection: ')
    return user_input

def select_menu():
    print('\n[ 1 ] Download')
    print('[ 0 ] Exit\n')

    user_input = input('Selection: ')
    return user_input

def get_web_version(poolManager):
    url = 'https://www.subdivx.com/'
    request = poolManager.request('GET', url)

    label = 'id="vs">'

    try:
        response_data = request.data.decode('utf-8')

        version_start_index = response_data.find(label) + len(label)
        version_end_index = response_data.find('</div>', version_start_index)

        version_text = response_data[version_start_index:version_end_index]

        version = version_text.replace('v', '').replace('.', '')

        return version
    except Exception as error:
        helper.logger.error(error)

def delay(factor=2):
    delay = 2 ** factor # default value delay is 4 seconds
    time.sleep(delay)

##############################################################################
# Cookie functions
##############################################################################

cookie_name = 'sdx-dl'

def exist_cookie():
    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, cookie_name)

    return os.path.exists(cookie_path)

def read_cookie():
    helper.logger.info('Read cookie')

    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, cookie_name)

    with open(cookie_path, 'r') as file:
        return file.read()

def get_cookie(poolManager, url):
    helper.logger.info('Get cookie from %s', url)

    # Request petition GET
    response = poolManager.request('GET', url, timeout=10)

    # Get cookie from response
    cookie = response.headers.get('Set-Cookie')

    # Split cookie
    cookie_parts = cookie.split(';')

    # Return sdx_cookie
    return cookie_parts[0]

def save_cookie(sdx_cookie):
    # Save cookie in temporary folder
    temp_dir = tempfile.gettempdir()
    cookie_path = os.path.join(temp_dir, cookie_name)

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
    cookie_path = os.path.join(temp_dir, cookie_name)

    if os.path.exists(cookie_path):
        os.remove(cookie_path)

def get_token(poolManager, url):
    helper.logger.info('Get token')

    response = poolManager.request('GET', url + 'inc/gt.php?gt=1')
    data = response.data

    token = json.loads(data)['token']

    return token

