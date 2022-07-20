import urllib3
import pandas as pd
import re
import sys
from bs4 import BeautifulSoup

# Options pandas
pd.set_option('colheader_justify', 'center')
pd.set_option('display.max_rows', None)

SUBDIVX_MAIN_URL = "https://www.subdivx.com/index.php"

FIND_SUBTITLE = sys.argv[1]

payload = {
    "buscar2": FIND_SUBTITLE,
    "accion": "5",
    "masdesc": "",
    "subtitulos": "1",
    "realiza_b": "1",
}

http = urllib3.PoolManager()
request = http.request('POST', SUBDIVX_MAIN_URL, fields=payload)

page = BeautifulSoup(request.data, 'html.parser')

results_descriptions = page.find_all('div', id='buscador_detalle_sub')
results_url = page.find_all('a', {'class': 'titulo_menu_izq'})
results_downloads = page.find_all('div', id='buscador_detalle_sub_datos')
results_user = page.find_all('a', {'class': 'link1'})

if not results_descriptions:
	print('No suitable subtitles')

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

sizeText = 100
for description in results_descriptions:
	text = description.get_text()
	shortText = text[:sizeText]
	descriptionList.append(shortText)

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

# Table (id, tittle, description, downloads, date, user)
df = pd.DataFrame({'Tittle':tittleList, 'Description':descriptionList, 'Downloads':downloadList, 'Date':dateList, 'User':userList})

print(df)