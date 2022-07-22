from subprocess import Popen
import zipfile

location = '.temp/'

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
                      z.extract(file)
            print('Extraction sucessfull subtittle enjoy!\n', file)
   except:
       print('Invalid file')

def unrar(fileRar):
    devnull = open('/dev/null', 'w')

    args = ['unrar', 'x', fileRar]
    sp = Popen(args, stdout=devnull)
    sp.wait()

def renameFile(newName):
   pass
