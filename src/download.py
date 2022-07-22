from subprocess import Popen
import zipfile

def downloadFile(url):
  location = '.temp/'
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
            print('Successfully extrated ', file)
   except:
       print('Invalid file')

def unrar(file):
   pass

def renameFile(newName):
   pass
