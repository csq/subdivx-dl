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

subtitleExtensions = ('.srt', '.SRT', '.sub', '.ass', '.ssa', 'idx')

def getTerminalWidth():
    try:
        terminalSize = shutil.get_terminal_size()
        return terminalSize.columns
    except OSError:
        return 80

def getFileExtension(filePath):
    with open(filePath, 'rb') as file:
        header = file.read(4)

        fileSignatures = {
            b'\x50\x4B\x03\x04': '.zip',
            b'\x52\x61\x72\x21': '.rar'
        }

        for signature, extension in fileSignatures.items():
            if header.startswith(signature):
                return extension

        return '.bin'

def downloadFile(poolManager, url, location):
    helper.logger.info('Downloading archive from: %s in %s', url, location)

    success = False

    with NamedTemporaryFile(dir=location, delete=False) as tempFile:
        for i in range(9, 0, -1):
            address = url[:20] + 'sub' + str(i) + '/' + url[20:]
            helper.logger.info('Attempt on server N°%d with url %s', i, address)

            response = poolManager.request('GET', address, preload_content=False)
            tempFile.write(response.data)
            tempFile.seek(0)

            fileExtension = getFileExtension(tempFile.name)

            if fileExtension in ('.zip', '.rar'):
                helper.logger.info('Download complete')

                newFilePath = tempFile.name + fileExtension
                tempFile.close()
                os.rename(tempFile.name, newFilePath)

                success = True
                break
            else:
                success = False

        if not success:
            print(f'No suitable subtitles download for: {url}')

def unzip(fileZip, destination):
    try:
        with ZipFile(fileZip, 'r') as z:
            helper.logger.info('Unpacking zip [%s]', os.path.basename(z.filename))
            for file in z.namelist():
                if (file.endswith(subtitleExtensions)):
                    helper.logger.info('Unzip [%s]', os.path.basename(file))
                    z.extract(file, destination)
            z.close()
    except:
        helper.logger.error('File corrupt')
        print('Invalid file')
    else:
        moveAllToParentFolder(destination)

def moveAllToParentFolder(pathDir):
    for (root, dirs, files) in os.walk(pathDir, topdown=True):
        for d in dirs:
            if (d != '__MACOSX'):
                subfolder = os.path.join(pathDir, dirs[0])
                for (root, dirs, files) in os.walk(subfolder, topdown=True):
                    for name in files:
                        shutil.copy(os.path.join(root, name), os.path.join(pathDir, name))

def unrar(fileRar, destination):
    helper.logger.info('Unpacking rar [%s] in %s', os.path.basename(fileRar), destination)
    rf = RarFile(fileRar)

    for file in rf.namelist():
        if (file.endswith(subtitleExtensions)):
            helper.logger.info('Unrar [%s]', os.path.basename(file))
            rf.extract(file, destination)
    rf.close()

def printMenuContentDir(args, pathDir):
    header = [['N°', 'File name']]
    files = os.listdir(pathDir)

    data = []

    index = 1
    x = 0
    while (x < len(files)):
        if (files[x].endswith(subtitleExtensions)):
            data.append(index)
            data.append(os.path.basename(files[x]))
            header.append(data[:])
            data.clear()
            index += 1
        x += 1

    if (index > 2):
        while (True):
            # Clear screen
            clear()

            # Print table with of the subtitles avaliable
            if (args.grid == False):
                print(tabulate(header, headers='firstrow', tablefmt='pretty', stralign='left'))
            else:
                print(tabulate(header, headers='firstrow', tablefmt='fancy_grid', stralign='left'))

            userInput = selectMenu()

            try:
                selection = int(userInput) - 1
                fileName = header[selection+1][1]
            except ValueError:
                print('\nInput only numbers')
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
                # Remove temp folder
                try:
                    shutil.rmtree(pathDir)
                    helper.logger.info('Delete temporal directory %s', pathDir)
                except OSError as error:
                    helper.logger.error(error)
                clear()
                exit(0)

            # Return the filename of the selected subtitle file
            clear()
            return fileName
    else:
        # Return the filename of the subtitle, excluding .zip or .rar extensions
        for x in range(2):
            if (files[x].endswith(subtitleExtensions)):
                return os.path.basename(files[x])

def movieSubtitle(args, pathFile, destination):
    helper.logger.info('Move subtitle to %s', destination)

    fileNameSelect = printMenuContentDir(args, pathFile)
    pathFileSelect = os.path.join(pathFile, fileNameSelect)

    # Rename file
    searchName, fileExtension = os.path.splitext(args.SEARCH)
    newName = searchName.strip()

    # Get file extension of subtitle downloaded
    subtitleFileExtension = os.path.splitext(pathFileSelect)[1]

    if (args.no_rename == False):
        newName = os.path.join(destination, f'{newName}{subtitleFileExtension}')
        helper.logger.info('Rename and move subtitle [%s] to [%s]', os.path.basename(pathFileSelect), os.path.basename(newName))

        os.makedirs(os.path.dirname(newName), exist_ok=True)

        try:
            shutil.copy(pathFileSelect, newName)
        except PermissionError:
            if (args.verbose != True):
                clear()
                print('You do not have permissions to write here ', os.path.dirname(newName))
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

    else:
        newName = os.path.join(destination, os.path.basename(pathFileSelect))
        helper.logger.info('Just move subtitle [%s] to [%s]', os.path.basename(pathFileSelect), destination)

        os.makedirs(os.path.dirname(newName), exist_ok=True)

        try:
            shutil.copy(pathFileSelect, newName)
        except PermissionError:
            if (args.verbose != True):
                clear()
                print('You do not have permissions to write here ', os.path.dirname(newName))
            helper.logger.warning('Permissions issues on destination directory')
            exit(0)

def tvShowSubtitles(args, pathFile, destination):
    helper.logger.info('Moves subtitles to %s', destination)
    files = os.listdir(pathFile)

    # TV series season and episode names
    patternSeriesTv = r'(.*?)[.\ssS](\d{1,2})[eExX](\d{1,3}).*'

    index = 0

    while (index < len(files)):
        fileSrc = os.path.join(pathFile, files[index])
        subtitleFileExtension = os.path.splitext(files[index])[1]

        if (files[index].endswith(subtitleExtensions) and (args.no_rename != True)):
            result = re.search(patternSeriesTv, files[index])

            try:
                getTvShow = result.group(1)
                getSeason = result.group(2)
                getEpisode = result.group(3)

                serie = getTvShow
                season = 'S' + getSeason
                episode = 'E' + getEpisode

                exclude = ['.', '-']
                for i in exclude:
                    serie = serie.replace(i, ' ')

                # Remove double spaces and end space in name tv show
                serie = serie.replace('  ', '').rstrip()

                # Format name example:
                # Serie - S05E01.srt | S05E01.srt
                if (serie != ''):
                    newName = serie + ' - ' + season + episode + subtitleFileExtension
                else:
                    newName = season + episode + subtitleFileExtension

            except Exception as e:
                helper.logger.error(e)
                fileDst = os.path.join(destination, files[index])
                helper.logger.info('No match Regex: Just move subtitle [%s]', files[index])

                os.makedirs(os.path.dirname(fileDst), exist_ok=True)

                try:
                    shutil.copy(fileSrc, fileDst)
                except PermissionError:
                    if (args.verbose != True):
                        clear()
                        print('You do not have permissions to write here ', os.path.dirname(fileDst))
                    helper.logger.warning('Permissions issues on destination directory')
                    exit(0)
            else:
                fileDst = os.path.join(destination, newName)
                helper.logger.info('Move subtitle [%s] as [%s]', files[index], newName)

                os.makedirs(os.path.dirname(fileDst), exist_ok=True)

                try:
                    shutil.copy(fileSrc, fileDst)
                except PermissionError:
                    if (args.verbose != True):
                        clear()
                        print('You do not have permissions to write here ', os.path.dirname(fileDst))
                    helper.logger.warning('Permissions issues on destination directory')
                    exit(0)

        # Move (rename same name for override) files without rename if flag --no-rename is True
        elif (files[index].endswith(subtitleExtensions)):
            fileDst = os.path.join(destination, files[index])
            helper.logger.info('Move subtitle [%s] to [%s]',  files[index], destination)

            os.makedirs(os.path.dirname(fileDst), exist_ok=True)

            try:
                shutil.copy(fileSrc, fileDst)
            except PermissionError:
                if (args.verbose != True):
                    clear()
                    print('You do not have permissions to write here ', os.path.dirname(fileDst))
                helper.logger.warning('Permissions issues on destination directory')
                exit(0)
        index += 1

def renameAndMoveSubtitle(args, pathFile, destination):
    # Check flag --season
    if (args.season == False):
        # Rename single srt
        movieSubtitle(args, pathFile, destination)
    else:
        # Move and rename bulk srt
        tvShowSubtitles(args, pathFile, destination)

def getDataPage(args, poolManager, url, token, search):
    print('Searching...', end='\r')

    query = parseSearchQuery(search)
    version = getWebVersion(poolManager)

    payload = {
        'tabla': 'resultados',
        'filtros': '',
        f'buscar{version}': query,
        'token': token
    }

    helper.logger.info('Starting request to subdivx.com with search: %s parsed as: %s', search, query)

    maxAttempts = 3
    searchResults = []

    for attempt in range(maxAttempts):
        helper.logger.info('Attempt number %s', attempt + 1)

        if attempt > 0:
            delay()

        request = poolManager.request('POST', url=url, fields=payload)

        try:
            data = json.loads(request.data).get('aaData')
        except JSONDecodeError:
            clear()
            print('Subtitles not found because cookie expired')
            deleteCookie()
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
                'upload_date': parseDate(result['fecha_subida']) if result['fecha_subida'] else '-'
            }
            searchResults.append(subtitle)

        if not searchResults and attempt < (maxAttempts - 1):
            continue
        elif searchResults:
            helper.logger.info('Subtitles found for: %s', query)
            break
        elif not searchResults and attempt == maxAttempts - 1:
            helper.logger.info('Subtitles not found for: %s', query)
            if (args.verbose != True):
                print('Subtitles not found')
            exit(0)

    return searchResults

def sortData(args, data):
    if (args.order_by_downloads == True):
        return sorted(data, key=lambda item: item['downloads'], reverse=True)
    elif (args.order_by_dates == True):
        sortedData = sorted(
            data,
            key=lambda item: (
                datetime.datetime.strptime(item['upload_date'], '%d/%m/%Y'
                if item['upload_date'] != '-' else '-')
            ),
            reverse=True
        )
        return sortedData

def parseDate(date):
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
    except ValueError:
        return None

def parseSearchQuery(search):
    try:
        result = guessit(search)
        fileType = result['type']
        title = result['title']
        year = result.get('year', '')
        season = result.get('season', '')
        episode = result.get('episode', '')
    except KeyError:
        return search

    if fileType == 'episode':
        try:
            episodeNumber = f'E{episode:02d}' if episode else ''
            query = f'{title} S{season:02d}{episodeNumber}'
        except ValueError:
            return search
    else:
        query = f'{title} {year}'

    return query

def getComments(poolManager, url, idSub):

    payload = {
        'getComentarios': idSub
    }

    request = poolManager.request('POST', url, fields=payload)

    try:
        data = json.loads(request.data).get('aaData')
    except JSONDecodeError:
        print('Comments not found')
        helper.logger.error('Response could not be serialized')
        exit(0)

    commentList = []

    for key in data:
        commentList.append(key['comentario'])

    return commentList

def printSearchResult(args, searchData):
    # Get terminal width
    terminalwidth = getTerminalWidth()

    # Initialize header
    data = [['N°', 'Title', 'Downloads', 'Date', 'User']]

    # Iterate over search results
    for index, item in enumerate(searchData, start=1):

        # Shorten title if necessary
        if args.grid:
            title = textwrap.shorten(item['title'], width=terminalwidth - 40, placeholder="...")
        else:
            title = textwrap.shorten(item['title'], width=terminalwidth - 55, placeholder="...")

        # Create row for table
        row = [index, title, item['downloads'], item['upload_date'], item['uploader']]

        # Append row to data
        data.append(row)

    # Print table
    if args.grid:
        print(tabulate(data, headers='firstrow', tablefmt='fancy_grid', colalign=('center', 'center','decimal', 'center', 'center')))
    else:
        print(tabulate(data, headers='firstrow', tablefmt='pretty', colalign=('center', 'center','decimal')))

def printSelectDescription(args, selection, searchData):
    # Get terminal width
    terminalwidth = getTerminalWidth()

    # Initialize header
    descriptionSelect = [['Description']]

    # Get description
    description = searchData[selection]['description'].strip()
    descriptionSelect.append([description])

    # Print table
    if args.grid:
        print(tabulate(descriptionSelect, headers='firstrow', tablefmt='fancy_grid', stralign='left', maxcolwidths=[terminalwidth - 5]))
    else:
        print(tabulate(descriptionSelect, headers='firstrow', tablefmt='pretty', stralign='left', maxcolwidths=[terminalwidth - 5]))

def getSubtitle(args, poolManager, url):
    if (args.verbose != True):
        print('Working...')

    # Check flag --location
    LOCATION_DESTINATION = args.location

    # Create temporal directory
    tempdir = tempfile.TemporaryDirectory()
    fpath = tempdir.name
    helper.logger.info('Create temporal directory %s', fpath)

    # Download zip/rar in temporal directory
    downloadFile(poolManager, url, fpath)

    # Determinate final path for subtitle
    if (LOCATION_DESTINATION == None):
        parentFolder = os.getcwd()
    else:
        parentFolder = LOCATION_DESTINATION

    # In case the server does not return a file, exit
    listDirectory = os.listdir(fpath)

    if not listDirectory:
        helper.logger.info('Remote server not found file')

        helper.logger.info('Delete temporal directory %s', fpath)
        tempdir.cleanup()

        if (args.verbose != True):
            clear()
            print('Subtitle not found because server missing file')
        exit(0)

    # Extract zip/rar file
    for file in listDirectory:
        pathFile = os.path.join(fpath, file)

        if (file.endswith('.zip')):
            unzip(pathFile, fpath)
        elif (file.endswith('.rar')):
            unrar(pathFile, fpath)

    # Rename and/or move subtitles
    renameAndMoveSubtitle(args, fpath, parentFolder)

    # Remove temp folder
    try:
        tempdir.cleanup()
        helper.logger.info('Delete temporal directory %s', fpath)
    except OSError as error:
        helper.logger.error(error)

    if (args.verbose != True):
        clear()
        print('Done')

def printSelectComments(args, commentList):
    # Get terminal width
    terminalwidth = getTerminalWidth()

    # Initialize header
    header = ['N°', 'Comments']
    comment = []

    # Iterate over comments
    for index, text in enumerate(commentList, start=1):
        comment.append([index, text.strip()])

    # Print table
    if args.grid:
        print(tabulate(comment, headers=header, tablefmt='fancy_grid', colalign=('center', 'left'), maxcolwidths=[None, terminalwidth - 12]))
    else:
        print(tabulate(comment, headers=header, tablefmt='pretty', colalign=('center', 'left'), maxcolwidths=[None, terminalwidth - 10]))

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def mainMenu():
    print('\n[1~9] Select')
    print('[ 0 ] Exit\n')

    userInput = input('Selection: ')
    return userInput

def selectMenu():
    print('\n[ 1 ] Download')
    print('[ 0 ] Exit\n')

    userInput = input('Selection: ')
    return userInput

def getWebVersion(poolManager):
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

cookieName = 'sdx-dl'

def existCookie():
    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    return os.path.exists(cookiePath)

def readCookie():
    helper.logger.info('Read cookie')

    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    with open(cookiePath, 'r') as file:
        return file.read()

def getCookie(poolManager, url):
    helper.logger.info('Get cookie from %s', url)

    # Request petition GET
    response = poolManager.request('GET', url, timeout=10)

    # Get cookie from response
    cookie = response.headers.get('Set-Cookie')

    # Split cookie
    cookieParts = cookie.split(';')

    # Return sdxCookie
    return cookieParts[0]

def saveCookie(sdxCookie):
    # Save cookie in temporary folder
    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    with open(cookiePath, 'w') as file:
        file.write(sdxCookie)
        file.close()

    helper.logger.info('Save cookie')

def setCookie(poolManager, url, header):
    cookie = None

    if not existCookie():
        cookie = getCookie(poolManager, url)
        saveCookie(cookie)
    else:
        cookie = readCookie()

    header['cookie'] = cookie

def deleteCookie():
    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    if os.path.exists(cookiePath):
        os.remove(cookiePath)

def getToken(poolManager, url):
    helper.logger.info('Get token')

    data = poolManager.request('GET', url+'inc/gt.php?gt=1', preload_content=False).data

    token = json.loads(data)['token']

    return token

