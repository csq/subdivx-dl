# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import zipfile
import shutil
import json
import time
import sys
import os
import re

from tabulate import tabulate
from subdivx_dl import helper
from subprocess import PIPE, Popen

SUCCESSFULL = '0'

def downloadFile(userAgent, url, location):
    helper.logging.info('Downloading archive from: %s in %s', url, location)

    sv = 9
    stop = False

    while(stop is False):
        address = url[:20] + 'sub'+ str(sv) + '/' + url[20:]

        cmd1 = 'wget --user-agent=' + '"{}"'.format(userAgent['user-agent']) + ' -qcP ' + location +' '+ address + '.zip ; echo $?'
        cmd2 = 'wget --user-agent=' + '"{}"'.format(userAgent['user-agent']) + ' -qcP ' + location +' '+ address + '.rar ; echo $?'
        
        process = Popen("{}; {}".format(cmd1, cmd2), shell=True, stdout=PIPE, text=True)
        process.wait()
        response = process.communicate()[0]

        helper.logging.info('Attempt on sv N°%d with url %s', sv, address)

        if (SUCCESSFULL in response):
            stop = True
        elif(sv == 1):
            stop = True
        
        sv = sv - 1

def unzip(fileZip, destination):
    try:
        with zipfile.ZipFile(fileZip, 'r') as z:
            helper.logging.info('Unpacking zip [%s]', os.path.basename(z.filename))
            for file in z.namelist():
                if file.endswith(('.srt', '.SRT')):
                    z.extract(file, destination)
    except:
        helper.logging.error('File corrupt')
        print('Invalid file')
    else:
        moveAllToParentFolder(destination)

def moveAllToParentFolder(pathDir):
    for (root, dirs, files) in os.walk(pathDir, topdown=True):
        for d in dirs:
            if d != '__MACOSX':
                subfolder = os.path.join(pathDir, dirs[0])
                for (root, dirs, files) in os.walk(subfolder, topdown=True):
                    for name in files:
                        os.rename(os.path.join(root, name), os.path.join(pathDir, name))

def unrar(fileRar, destination):
    helper.logging.info('Unpacking rar [%s] in %s', os.path.basename(fileRar), destination)
    args = ['unrar', 'e', '-r', '-inul', '-o+', fileRar, destination]
    sp = Popen(args)
    sp.wait()

def printMenuContentDir(args, pathDir):
    header = [['N°', 'File name']]
    files = os.listdir(pathDir)

    data = []

    index = 1
    x = 0
    while (x < len(files)):
        if files[x].endswith(('.srt', '.SRT')):
            data.append(index)
            data.append(os.path.basename(files[x]))
            header.append(data[:])
            data.clear()
            index = index + 1
        x = x + 1

    if index > 2:
        while(True):
            # Clear screen
            clear()
            
            # Print table with of the subtitles avaliable
            if (args.grid == False):
                print(tabulate(header, headers='firstrow', tablefmt='pretty', stralign='left'))
            else:
                print(tabulate(header, headers='firstrow', tablefmt='fancy_grid', stralign='left'))

            print('\n[1~9] Select')
            print('[ 0 ] Exit\n')

            try:
                selection = int(input('Selection: '))-1
                fileName = header[selection+1][1]
            except ValueError:
                print('\nInput only numbers')
                time.sleep(1)
                continue
            except IndexError:
                print('\nInput valid numbers')
                time.sleep(1)
                continue

            if selection < -1:
                print('\nInput only positive numbers')
                time.sleep(1)
                continue
            elif selection == -1:
                # Remove temp folder
                try:
                    shutil.rmtree(pathDir)
                    helper.logging.info('Delete temporal directory %s', pathDir)
                except OSError as error:
                    helper.logging.error(error)
                clear()
                exit(0)

            # Return name file with extension .srt selected
            return fileName
    else:
        # Return name file with extension .srt exclude .zip or .rar
        for x in range(2):
            if files[x].endswith(('.srt', '.SRT')):
                return os.path.basename(files[x])

def movieSubtitle(args, pathFile, destination):
    fileNameSelect = printMenuContentDir(args, pathFile)
    pathFileSelect = os.path.join(pathFile, fileNameSelect)
    
    helper.logging.debug('Moves subtitles to %s', destination)
    newName = args.SEARCH

    if args.no_rename == False:
        new_name = os.path.join(destination, f'{newName}.srt')
        helper.logging.info('Rename and move subtitle [%s] to [%s]', os.path.basename(pathFileSelect), os.path.basename(new_name))
        os.rename(pathFileSelect, new_name)
    else:
        new_name = os.path.join(destination, os.path.basename(pathFileSelect))
        helper.logging.info('Just move subtitle [' + os.path.basename(pathFileSelect) + '] to [' + destination + ']')
        os.rename(pathFileSelect, new_name)

def tvShowSubtitles(args, pathFile, destination):
    helper.logging.debug('Moves subtitles to %s', destination)
    files = os.listdir(pathFile)

    # TV series season and episode names
    pattern_series_tv = '(.*?)[.\ssS](\d{1,2})[eExX](\d{1,3}).*'

    index = 0

    while (index < len(files)):
        file_src = os.path.join(pathFile, files[index])

        if (files[index].endswith('.srt') and (args.no_rename != True)):
            result = re.search(pattern_series_tv, files[index])

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
                    new_name = serie + ' - ' + season + episode + '.srt'
                else:
                    new_name = season + episode + '.srt'

            except Exception as e:
                helper.logging.error(e)
                file_dst = os.path.join(destination, files[index])
                helper.logging.info('No match Regex: Just move subtitle [' + files[index] + ']')
                os.rename(file_src, file_dst)
            else:
                file_dst = os.path.join(destination, new_name)
                helper.logging.info('Move subtitle [' + files[index] + '] as [' + new_name + ']')
                os.rename(file_src, file_dst)

        # Move (rename same name for override) files without rename if flag --no-rename is True
        elif files[index].endswith('.srt'):
            file_dst = os.path.join(destination, files[index])
            helper.logging.info('Move subtitle [' + files[index] + '] to [' + destination + ']')
            os.rename(file_src, file_dst)
        index = index + 1

def renameAndMoveSubtitle(args, pathFile, destination):
    # Check flag --season
    if (args.season == False):
        # Rename single srt
        movieSubtitle(args, pathFile, destination)
    else:
        # Move and rename bulk srt
        tvShowSubtitles(args, pathFile, destination)

def getDataPage(args, poolManager, url, search):

    payload = {
        'buscar': search,
        'filtros': '',
        'tabla': 'resultados'
    }

    helper.logging.debug('Starting request to subdivx.com with search query: %s', search)
    request = poolManager.request('POST', url, fields=payload)

    try:
        data = json.loads(json.dumps(request.json().get('aaData')))
    except JSONDecodeError:
        print('Subtitles not found')
        helper.logging.error('Response could not be serialized')
        sys.exit(0)

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
        if match is None:
            dateList.append('-')
        else:
            dateList.append(match.group(1))

    if not idList:
        print('Subtitles not found')
        helper.logging.info('Subtitles not found for %s', search)
        sys.exit(0)

    return titleList, descriptionList, idList, downloadList, userList, dateList

def getComments(poolManager, url, id_sub):

    payload = {
        'getComentarios': id_sub
    }

    request = poolManager.request('POST', url, fields=payload)

    try:
        data = json.loads(json.dumps(request.json().get('aaData')))
    except JSONDecodeError:
        print('Comments not found')
        helper.logging.error('Response could not be serialized')
        sys.exit(0)

    commentList = []

    index = 1
    for key in data:
        commentList.append([index, key['comentario']])
        index = index + 1 

    return commentList

def printSearchResult(args, titleList, downloadList, dateList, userList):
    # Mix data
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
        index = index + 1

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(data, headers='firstrow', tablefmt='pretty', colalign=('center', 'center','decimal')))
    else:
        print(tabulate(data, headers='firstrow', tablefmt='fancy_grid', colalign=('center', 'center','decimal', 'center', 'center')))

def printSelectDescription(args, selection, descriptionList):
    description_select = [['Description']]
    aux = descriptionList[selection].splitlines()
    words = aux[0].split()

    maxLengh =  10
    line = ''
    count = 0

    for word in words:
        if (count <= maxLengh):
            line = line+' '+word
            count = count + 1
        else:
            a = line+' '+word
            description_select.append([a])
            line = ''
            count = 0
    description_select.append([line])

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(description_select, headers='firstrow', tablefmt='pretty', stralign='center'))
    else:
        print(tabulate(description_select, headers='firstrow', tablefmt='fancy_outline', stralign='center'))

def getSubtitle(userAgent, args, url):
    print('Working ...')

    # Check flag --location
    LOCATION_DESTINATION = args.location
    
    if (LOCATION_DESTINATION == None):
        fpath = os.path.join(os.getcwd(), '.tmp', '')
        downloadFile(userAgent, url, fpath)
        parent_folder = os.getcwd()
    else:
        fpath = os.path.join(LOCATION_DESTINATION, '.tmp', '')
        downloadFile(userAgent, url, fpath)
        parent_folder = LOCATION_DESTINATION

    try:
        listDirectory = os.listdir(fpath)
    except FileNotFoundError:
        print('Subtitle not found because server missing file')
        helper.logging.info('Remote server not found file')
        exit(0)


    for file in listDirectory:
        pathFile = os.path.join(fpath, file)

        if (file.endswith('.zip')):
            unzip(pathFile, fpath)
        elif (file.endswith('.rar')):
            unrar(pathFile, fpath)

    # Rename and/or move subtitles
    renameAndMoveSubtitle(args, fpath, parent_folder)

    # Remove temp folder
    try:
        shutil.rmtree(fpath)
        helper.logging.info('Delete temporal directory %s', fpath)
    except OSError as error:
        helper.logging.error(error)

    clear()
    print('Done')

def printSelectComments(args, commentList):
    header = ['N°', 'Comments']

    # Check flag --grid
    if (args.grid == False):
        print(tabulate(commentList, header, tablefmt='pretty', stralign='left'))
    else:
        print(tabulate(commentList, header, tablefmt='fancy_outline', stralign='left'))

def clear():
    os.system('clr' if os.name == 'nt' else 'clear')

# Menu section
def mainMenu():
    print('\n[1~9] Select')
    print('[ 0 ] Exit\n')
