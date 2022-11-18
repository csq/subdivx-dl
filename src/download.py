from subprocess import Popen
import zipfile
import os

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
