# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import logging
import zipfile
import shutil
import time
import sys
import os
import re

from subprocess import Popen
from bs4 import BeautifulSoup
from tabulate import tabulate

# Parser for command-line
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Subdvix-dl is a subtitle downloader for the website subdvix.com',
    epilog='''Disclaimer: subdvix.com not involve in this development.\n
            \rAny comments about this software make it in:\n \
            \r<www.github.com/csq/subdivx-dl> or <www.gitlab.com/csq1/subdivx-dl>'''
)

parser.add_argument('SEARCH', help='name of the tv serie or movie to search for subtitle')
parser.add_argument('-v', '--version', action='version', version='2022.12.12')
parser.add_argument('-s', '--season', help='download full season subtitles', action='store_true')
parser.add_argument('-l', '--location', help='destination directory')
parser.add_argument('-nr', '--no-rename', help='disable rename files', action='store_true')
parser.add_argument('--order-by-downloads', help='order results by downloads', action='store_true')
parser.add_argument('--order-by-dates', help='order results by dates', action='store_true')

# Create and configure logger
logging.basicConfig(
    filename='/tmp/subdivx-dl.log',
    filemode='w',
    encoding='utf-8',
    level=logging.DEBUG,
    format='[%(asctime)s] |%(levelname)s| %(message)s',
    datefmt='%d/%m/%y %H:%M:%S'
)

def downloadFile(url, location):
    logging.info('Downloading archive from: %s in %s', url, location)
    args = ['wget', '--content-disposition', '-q', '-c', '-P', location, url]
    output = Popen(args)
    output.wait()

def unzip(fileZip, destination):
    try:
        with zipfile.ZipFile(fileZip, 'r') as z:
            logging.info('Unpacking zip [%s]', os.path.basename(z.filename))
            for file in z.namelist():
                if file.endswith('.srt'):
                    z.extract(file, destination)
    except:
        logging.error('File corrupt')
        print('Invalid file')

def unrar(fileRar, destination):
    logging.info('Unpacking rar [%s] in %s', os.path.basename(fileRar), destination)
    args = ['unrar', 'x', '-inul', '-o+', fileRar, destination]
    sp = Popen(args)
    sp.wait()

def printMenuContentDir(pathDir):
    header = [['N??', 'File name']]
    files = os.listdir(pathDir)

    data = []

    index = 1
    x = 0
    while (x < len(files)):
        if files[x].endswith('.srt'):
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
            print(tabulate(header, headers='firstrow', tablefmt='pretty', stralign='left'))
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
                    logging.info('Delete temporal directory %s', pathDir)
                except OSError as error:
                    logging.error(error)
                clear()
                exit(0)

            # Return name file with extension .srt selected
            return fileName
    else:
        # Return name file with extension .srt exclude .zip or .rar
        for x in range(2):
            if files[x].endswith('.srt'):
                return os.path.basename(files[x])

def movieSubtitle(args, pathFile, destination):
    fileNameSelect = printMenuContentDir(pathFile)
    pathFileSelect = os.path.join(pathFile, fileNameSelect)
    
    logging.debug('Moves subtitles to %s', destination)
    newName = args.SEARCH

    if args.no_rename == False:
        new_name = os.path.join(destination, f'{newName}.srt')
        logging.info('Rename and move subtitle [%s] to [%s]', os.path.basename(pathFileSelect), os.path.basename(new_name))
        os.rename(pathFileSelect, new_name)
    else:
        new_name = os.path.join(destination, os.path.basename(pathFileSelect))
        logging.info('Just move subtitle [' + os.path.basename(pathFileSelect) + '] to [' + destination + ']')
        os.rename(pathFileSelect, new_name)

def tvShowSubtitles(args, pathFile, destination):
    logging.debug('Moves subtitles to %s', destination)
    files = os.listdir(pathFile)

    # TV series season and episode names
    pattern_series_tv = '(.*?)[.\s][sS](\d{1,2})[eE](\d{1,3}).*'

    index = 0

    while (index < len(files)):
        file_src = os.path.join(pathFile, files[index])

        if (files[index].endswith('.srt') and (args.no_rename != True)):
            result = re.search(pattern_series_tv, files[index])

            try:
                get_name_serie = result.group(1)
                get_season = result.group(2)
                get_episode = result.group(3)

                serie = get_name_serie.replace('.',' ')
                season = 'S' + get_season
                episode = 'E' + get_episode

                # New name format example: Silicon Valley - S05E01.srt
                new_name = serie + ' - ' + season + episode + '.srt'
            except Exception as e:
                logging.error(e)
                file_dst = os.path.join(destination, files[index])
                logging.info('No match Regex: Just move subtitle [' + files[index] + ']')
                os.rename(file_src, file_dst)
            else:
                file_dst = os.path.join(destination, new_name)
                logging.info('Move subtitle [' + files[index] + '] as [' + new_name + ']')
                os.rename(file_src, file_dst)

        # Move (rename same name for override) files without rename if flag --no-rename is True
        elif files[index].endswith('.srt'):
            file_dst = os.path.join(destination, files[index])
            logging.info('Move subtitle [' + files[index] + '] to [' + destination + ']')
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
        "buscar2": search,
        "accion": "5",
        "masdesc": ""
    }

    # Check flag --order-by
    if args.order_by_downloads == True:
        payload["oxdown"] = "1"
    elif args.order_by_dates == True:
        payload["oxfecha"] = "2"

    logging.debug('Starting request to subdivx.com with search query: %s', search)
    request = poolManager.request('POST', url, fields=payload)
    page = BeautifulSoup(request.data, 'html.parser')

    results_descriptions = page.find_all('div', id='buscador_detalle_sub')
    results_url = page.find_all('a', {'class': 'titulo_menu_izq'})
    results_downloads = page.find_all('div', id='buscador_detalle_sub_datos')
    results_user = page.find_all('a', {'class': 'link1'})

    if not results_descriptions:
        print('Subtitles not found')
        logging.info('Subtitles not found for %s', search)
        sys.exit(0)

    titleList = list()
    descriptionList = list()
    urlList = list()
    downloadList = list()
    userList = list()
    dateList = list()

    separator = "Subtitulos de "
    for title in results_url:
        string = title.get_text()
        titleList.append(string[len(separator):])

    for description in results_descriptions:
        text = description.get_text()
        if text != '':
            descriptionList.append(text)
        else:
            descriptionList.append('Whitout description')

    for link in results_url:
        urlList.append(link.get('href'))

    patternNumber = '\d+(?:\,\d+)?'
    patternDate = '(\d+/\d+/\d+)'
    sizeText = 20
    for download in results_downloads:
        text = download.get_text()

        date = re.search(patternDate, text)
        if date != None:
            dateList.append(date.group())
        else:
            dateList.append('-')

        subText = text[:sizeText]
        downloadCount = re.search(patternNumber, subText)

        if downloadCount != None:
            downloadList.append(downloadCount.group())
        else:
            downloadCount.append('-')

    banWord = ["t????tulo", "fecha", "downloads", "subtitulos en espa????ol"]
    for user in results_user:
        userName = user.get_text()
        if userName not in banWord:
            userList.append(userName)

    return titleList, descriptionList, urlList, downloadList, userList, dateList

def printSearchResult(titleList, downloadList, dateList, userList):
    # Mix data
    data = [['N??', 'Title', 'Downloads', 'Date', 'User']]

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

    print(tabulate(data, headers='firstrow', tablefmt='pretty', colalign=('center', 'center','decimal')))

def printSelectDescription(selection, descriptionList):
    description_select = [['Description']]
    aux = descriptionList[selection].splitlines()
    words = aux[0].split()

    maxLengh =  10
    line = ""
    count = 0

    for word in words:
        if (count <= maxLengh):
            line = line+" "+word
            count = count + 1
        else:
            a = line+" "+word
            description_select.append([a])
            line = ""
            count = 0
    description_select.append([line])
    
    print(tabulate(description_select, headers='firstrow', tablefmt='pretty', stralign='center'))

def getSubtitle(args, request, url):
    print('Working ...')
    # Scrap page download srt
    page = BeautifulSoup(request.data, 'html.parser')
    urlFile = page.find('a', {'class': 'link1'})

    urlFileToDownload = url + urlFile.get('href')

    # Check flag --location
    LOCATION_DESTINATION = args.location
    
    if (LOCATION_DESTINATION == None):
        fpath = os.path.join(os.getcwd(), '.tmp', '')
        downloadFile(urlFileToDownload, fpath)
        parent_folder = os.getcwd()
    else:
        fpath = os.path.join(LOCATION_DESTINATION, '.tmp', '')
        downloadFile(urlFileToDownload, fpath)
        parent_folder = LOCATION_DESTINATION

    listDirectory = os.listdir(fpath)

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
        logging.info('Delete temporal directory %s', fpath)
    except OSError as error:
        logging.error(error)

    clear()
    print('Done')

def clear():
    os.system('clr' if os.name == 'nt' else 'clear')