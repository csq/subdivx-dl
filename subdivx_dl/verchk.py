# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
import urllib3

from subdivx_dl import __version__

class VersionChecker():
    def __init__(self):
        self.version = __version__

    def get_latest_version(self):
        url = 'https://raw.githubusercontent.com/csq/subdivx-dl/refs/heads/master/subdivx_dl/version.py'
        try:
            response = urllib3.request('GET', url)
        except Exception:
            print('\nFailed to check for updates\nPlease check your internet connection')
            exit(1)
        if response.status == 200:
            content = response.data.decode('utf-8')
            version_pattern = r"__version__ = '(\d+\.\d+\.\d+)'"
            match = re.search(version_pattern, content)
            return match.group(1)

    def check_version(self):
        latest_version = self.get_latest_version()
        if latest_version > self.version:
            print(f'New version available: {latest_version}')
        else:
            print('Using the latest version')

def run_check_version():
    checker = VersionChecker()
    print(f'Installed version: {checker.version}')
    checker.check_version()