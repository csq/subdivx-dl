import argparse
import logging
import zipfile
import shutil
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
parser.add_argument('-v', '--version', action='version', version='2022.07.31')
parser.add_argument('-s', '--season', help='download full season subtitles', action='store_true')
parser.add_argument('-l', '--location', help='destination directory')
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
    extension = '.srt'
    try:
        with zipfile.ZipFile(fileZip, 'r') as z:
            for file in z.namelist():
                if file.endswith(extension):
                    logging.info('Unpacking zip [%s]', os.path.basename(z.filename))
                    z.extract(file, destination)
    except:
        logging.error('File corrupt')
        print('Invalid file')

def unrar(fileRar, destination):
    logging.info('Unpacking rar [%s] in %s', os.path.basename(fileRar), destination)
    devnull = open('/dev/null', 'w')

    args = ['unrar', 'x', fileRar, destination]
    sp = Popen(args, stdout=devnull)
    sp.wait()

def renameFile(pathFile, destination, newName):
    logging.debug('Moves subtitles to %s', destination)
    files = os.listdir(pathFile)
    
    index = 0
    count = 0

    while (index < len(files)):
        if (files[index].endswith('.srt')):
            old_name = os.path.join(pathFile, files[index])

            if (count == 0):
                new_name = os.path.join(destination, f'{newName}.srt')
                logging.info('Rename and move subtitle [%s] to [%s]', os.path.basename(old_name), os.path.basename(new_name))
                os.rename(old_name, new_name)
                count = count + 1
            else:
                new_name = os.path.join(destination, f'{newName}-V{count}.srt')
                logging.info('Rename and move subtitle [%s] to [%s]', os.path.basename(old_name), os.path.basename(new_name))
                os.rename(old_name, new_name)
                count = count + 1
        index = index + 1

def moveFiles(pathFile, destination):
    logging.debug('Moves subtitles to %s', destination)
    files = os.listdir(pathFile)

    # TV series season and episode names
    pattern_series_tv = '(.*?)[.\s][sS](\d{1,2})[eE](\d{1,3}).*'

    index = 0

    while (index < len(files)):
        if (files[index].endswith('.srt')):
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
                print('Error: ', e)
            finally:
                pass

            file_src = os.path.join(pathFile, files[index])
            file_dst = os.path.join(destination, new_name)
            logging.info('Move subtitle [' + files[index] + '] as [' + new_name + ']')
            os.rename(file_src, file_dst)
        index = index + 1

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

    banWord = ["tÃ­tulo", "fecha", "downloads", "subtitulos en espaÃ±ol"]
    for user in results_user:
        userName = user.get_text()
        if userName not in banWord:
            userList.append(userName)

    return titleList, descriptionList, urlList, downloadList, userList, dateList

def printSearchResult(titleList, downloadList, dateList, userList):
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

    # Check flag --season
    if (args.season == False):
        # Rename single srt
        renameFile(fpath, parent_folder, args.SEARCH)
    else:
        # Move and rename bulk srt
        moveFiles(fpath, parent_folder)

    # Remove temp folder
    try:
        shutil.rmtree(fpath)
        logging.info('Delete temporal directory %s', fpath)
    except OSError as error:
        logging.error(error)

    print('Done')

def clear():
    os.system('clr' if os.name == 'nt' else 'clear')