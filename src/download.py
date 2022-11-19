from subprocess import Popen
import zipfile
import os
import re

location = '.temp/'
temp_dir = os.path.join(os.getcwd(), location, '')

def downloadFile(url):
  args = ['wget', '--content-disposition', '-q', '-c', '-P', location, url]
  output = Popen(args)
  output.wait()

def unzip(fileZip):
   extension = '.srt'
   try:
       with zipfile.ZipFile(fileZip, 'r') as z:
            for file in z.namelist():
                 if file.endswith(extension):
                      z.extract(file, temp_dir)
            print('Extraction sucessfull subtittle enjoy!\n', file)
   except:
       print('Invalid file')

def unrar(fileRar):
    devnull = open('/dev/null', 'w')

    args = ['unrar', 'x', fileRar, temp_dir]
    sp = Popen(args, stdout=devnull)
    sp.wait()

def renameFile(pathFile, newName):
    files = os.listdir(pathFile)

    index = 0
    count = 0

    while (index < len(files)):
        if (files[index].endswith('.srt')):
            old_name = os.path.join(pathFile, files[index])
            if (count == 0):
                new_name = os.path.join(os.getcwd(), f'{newName}.srt')
                os.rename(old_name, new_name)
                count = count + 1
            else:
                new_name = os.path.join(os.getcwd(), f'{newName}-V{count}.srt')
                os.rename(old_name, new_name)
                count = count + 1
        index = index + 1


def moveFiles(pathFile):
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
                print('Error: ', e)
            finally:
                pass

            file_src = os.path.join(pathFile, files[index])
            file_dst = os.path.join(os.getcwd(), new_name)
            os.rename(file_src, file_dst)
        index = index + 1
