#!/usr/bin/env python3

import urllib3
import pandas as pd
import re
import sys
import os
import shutil

from src.download import *
from bs4 import BeautifulSoup
from tabulate import tabulate

# Options pandas
pd.set_option('colheader_justify', 'center')
pd.set_option('display.max_rows', None)

SUBDIVX_MAIN_URL = "https://www.subdivx.com/index.php"
SUBDIVX_URL = "https://www.subdivx.com/"

if ((len(sys.argv)-1) == 0):
	sys.exit('Input any movie or serie name')
else:
	FIND_SUBTITLE = sys.argv[1]

http = urllib3.PoolManager()

def getDataPage(poolManager, url, search):

	payload = {
	    "buscar2": search,
	    "accion": "5",
	    "masdesc": "",
	    "subtitulos": "1",
	    "realiza_b": "1",
	}

	request = http.request('POST', url, fields=payload)
	page = BeautifulSoup(request.data, 'html.parser')

	results_descriptions = page.find_all('div', id='buscador_detalle_sub')
	results_url = page.find_all('a', {'class': 'titulo_menu_izq'})
	results_downloads = page.find_all('div', id='buscador_detalle_sub_datos')
	results_user = page.find_all('a', {'class': 'link1'})

	if not results_descriptions:
		print('No suitable subtitles')
		sys.exit(0)

	tittleList = list()
	descriptionList = list()
	urlList = list()
	downloadList = list()
	userList = list()
	dateList = list()

	separator = "Subtitulos de "
	for tittle in results_url:
		string = tittle.get_text()
		tittleList.append(string[len(separator):])

	for description in results_descriptions:
		text = description.get_text()
		descriptionList.append(text)

	for link in results_url:
		urlList.append(link.get('href'))

	patternNumber = '\d+(?:\,\d+)?'
	patternDate = '(\d+/\d+/\d+)'
	sizeText = 20
	for download in results_downloads:
		text = download.get_text()

		date = re.search(patternDate, text)
		if date != 'null':
			dateList.append(date.group())

		subText = text[:sizeText]
		downloadCount = re.search(patternNumber, subText)

		if downloadCount != 'null':
			downloadList.append(downloadCount.group())

	banWord = ["tÃ­tulo", "fecha", "downloads", "subtitulos en espaÃ±ol"]
	for user in results_user:
		userName = user.get_text()
		if userName not in banWord:
			userList.append(userName)

	return tittleList, descriptionList, urlList, downloadList, userList, dateList

def printSelectDescription(selection, descriptionList):
	description_select = []
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
			description_select.append(a)
			line = ""
			count = 0
	description_select.append(line)
	df_description = pd.DataFrame({'Description':description_select})
	print(tabulate(df_description, headers = 'keys', tablefmt = 'pretty', stralign='left'))

def getSubtitle(request, url):
	# Scrap page download srt
	page = BeautifulSoup(request.data, 'html.parser')
	urlFile = page.find('a', {'class': 'link1'})

	urlFileToDownload = url + urlFile.get('href')

	downloadFile(urlFileToDownload)

	# Clear screen
	clear()

	fpath = os.path.join(os.getcwd(), '.temp', '')
	listDirectory = os.listdir(fpath)

	for file in listDirectory:
		pathFile = os.path.join(fpath, file)

		if (file.endswith('.zip')):
			unzip(pathFile)
		elif (file.endswith('.rar')):
			unrar(pathFile)

	# Remove temp folder
	try:
		shutil.rmtree(fpath)
		print('Clear temp files\n')
	except OSError as error:
		print(error)

	# Rename bulk srt
	currentPath = os.getcwd()
	renameFile(currentPath, FIND_SUBTITLE)

def clear():
	os.system('clr' if os.name == 'nt' else 'clear')

tittleList, descriptionList, urlList, downloadList, userList, dateList = getDataPage(http, SUBDIVX_URL, FIND_SUBTITLE)

# Table (id, tittle, downloads, date, user)
df = pd.DataFrame({'Tittle':tittleList, 'Downloads':downloadList, 'Date':dateList, 'User':userList})

while (1):
	# Clear screen
	clear()
	
	# Display Search Results
	print(tabulate(df, headers = 'keys', tablefmt = 'pretty'))

	try:
		selection = int(input('\n[Selection] : '))
		request = http.request('GET', urlList[selection])
	except ValueError:
		sys.exit('Input only numbers')
	except IndexError:
	    sys.exit('input valid numbers')

	clear()
	printSelectDescription(selection, descriptionList)

	print('\n[1] Download subtitle')
	print('[2] Back\n')

	try:
		select_action = int(input('[Selection] : '))
	except ValueError:
		sys.exit('Input only numbers')

	if select_action == 1:
		getSubtitle(request, SUBDIVX_URL)
		exit(0)
	elif select_action == 2:
		clear()
