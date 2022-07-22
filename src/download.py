from subprocess import Popen, PIPE
import zipfile

def downloadFile(url):
  location = '.temp/'
  args = ['wget', '--content-disposition', '-q', '-c', '-P', location, url]
  output = Popen(args, stdout=PIPE)
  #stdout = output.communicate()

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
