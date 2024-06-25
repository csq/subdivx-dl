# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import tempfile
import shutil
import json
import time
import os
import re

from tabulate import tabulate
from subdivx_dl import helper
from json import JSONDecodeError
from tempfile import NamedTemporaryFile
from rarfile import RarFile
from zipfile import ZipFile
from guessit import guessit

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
                if (file.endswith(('.srt', '.SRT'))):
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
        if (file.endswith(('.srt', '.SRT'))):
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
        if (files[x].endswith(('.srt', '.SRT'))):
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

            # Return name file with extension .srt selected
            clear()
            return fileName
    else:
        # Return name file with extension .srt exclude .zip or .rar
        for x in range(2):
            if (files[x].endswith(('.srt', '.SRT'))):
                return os.path.basename(files[x])

def movieSubtitle(args, pathFile, destination):
    helper.logger.info('Move subtitle to %s', destination)

    fileNameSelect = printMenuContentDir(args, pathFile)
    pathFileSelect = os.path.join(pathFile, fileNameSelect)

    # Rename file
    searchName, fileExtension = os.path.splitext(args.SEARCH)
    newName = searchName.strip()

    if (args.no_rename == False):
        newName = os.path.join(destination, f'{newName}.srt')
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
    patternSeriesTv = '(.*?)[.\ssS](\d{1,2})[eExX](\d{1,3}).*'

    index = 0

    while (index < len(files)):
        fileSrc = os.path.join(pathFile, files[index])

        if (files[index].endswith('.srt') and (args.no_rename != True)):
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
                    newName = serie + ' - ' + season + episode + '.srt'
                else:
                    newName = season + episode + '.srt'

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
        elif (files[index].endswith('.srt')):
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

def getDataPage(args, poolManager, url, search):

    query = parseSearchQuery(search)

    payload = {
        'buscar': query,
        'filtros': '',
        'tabla': 'resultados'
    }

    helper.logger.info('Starting request to subdivx.com with search: %s parsed as: %s', search, query)
    request = poolManager.request('POST', url, fields=payload)

    try:
        data = json.loads(request.data).get('aaData')
    except JSONDecodeError:
        print('Subtitles not found')
        helper.logger.error('Response could not be serialized')
        exit(0)

    idList = list()
    titleList = list()
    descriptionList = list()
    downloadList = list()
    userList = list()
    dateList = list()

    for key in data:
        idList.append(key['id'])
        titleList.append(key['titulo'])
        descriptionList.append(key['descripcion'])
        downloadList.append(key['descargas'])
        userList.append(key['nick'])

        # Format date (year-month-day)
        match = re.search(r'(\d+-\d+-\d+)', str(key['fecha_subida']))
        if (match is None):
            dateList.append('-')
        else:
            dateList.append(match.group(1))

    if not idList:
        helper.logger.info('Subtitles not found for %s', query)
        if (args.verbose != True):
            print('Subtitles not found')
        exit(0)

    return titleList, descriptionList, idList, downloadList, userList, dateList

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
        episodeNumber = f'E{episode:02d}' if episode else ''
        query = f'{title} S{season:02d}{episodeNumber}'
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

def printSearchResult(args, titleList, downloadList, dateList, userList):
    data = [['N°', 'Title', 'Downloads', 'Date', 'User']]

    index = 1
    row = []

    while index <= len(titleList):
        row.append(index)
        row.append(titleList[index - 1])
        row.append(downloadList[index - 1])
        row.append(dateList[index - 1])
        row.append(userList[index - 1])
        data.append(row[:])
        row.clear()
        index += 1

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(data, headers='firstrow', tablefmt='pretty', colalign=('center', 'center','decimal')))
    else:
        print(tabulate(data, headers='firstrow', tablefmt='fancy_grid', colalign=('center', 'center','decimal', 'center', 'center')))

def printSelectDescription(args, selection, descriptionList):
    descriptionSelect = [['Description']]
    words = descriptionList[selection].split()

    maxLengh = 77
    count = 0

    line = ''
    for word in words:
        sizeWord = len(word)

        if (count + sizeWord <= maxLengh):
            line = '{} {}'.format(line, word)
            count = count + sizeWord
        elif (count + sizeWord > maxLengh):
                # Slice word
                missing = maxLengh - count
                sliceOne = word[:missing]
                sliceTwo = word[missing:]

                line = '{} {}'.format(line, sliceOne)
                count = count + len(sliceOne)

                if (count == maxLengh):
                    descriptionSelect.append([line])
                    line = '{}'.format(sliceTwo)
                    count = len(sliceTwo)
    descriptionSelect.append([line])

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(descriptionSelect, headers='firstrow', tablefmt='pretty', stralign='left'))
    else:
        print(tabulate(descriptionSelect, headers='firstrow', tablefmt='fancy_outline', stralign='left'))

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
    header = ['N°', 'Comments']
    comment = []

    maxLengh = 77

    for i in range(len(commentList)):
        words = commentList[i].split()

        count = 0
        line = ''

        for word in words:
            lenWord = len(word)

            if (count + lenWord < maxLengh):
                line = '{} {}'.format(line, word)
                count = count + lenWord
            elif (count + lenWord >= maxLengh):
                # Slice word
                slice = []

                missing = maxLengh - count
                slice = word[:missing]

                line = '{} {}'.format(line, slice)
                count = count + len(slice)
        comment.append([i + 1, line])

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(comment, headers=header, tablefmt='pretty', colalign=('center', 'left')))
    else:
        print(tabulate(comment, headers=header, tablefmt='fancy_outline', colalign=('center', 'left')))

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

##############################################################################
# Cookie functions
##############################################################################

cookieName = 'sdx-dl'

def getCookie(poolManager, url):
    helper.logger.info('Get cookie from %s', url)

    # Request petition GET
    response = poolManager.request('GET', url)

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

def existCookie():
    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    return os.path.exists(cookiePath)

def readCookie():
    helper.logger.info('Read cookie')

    tempDir = tempfile.gettempdir()
    cookiePath = os.path.join(tempDir, cookieName)

    with open(cookiePath, 'r') as file:
        cookie = file.read()

    return cookie

def setCookie(https, header, url):
    cookie = None

    if not existCookie():
        cookie = getCookie(https, url)
        saveCookie(cookie)
    else:
        cookie = readCookie()

    header['cookie'] = cookie
