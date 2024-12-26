import re
import requests

from .version import __version__

class VersionChecker():
    def __init__(self):
        self.version = __version__

    def get_latest_version(self):
        url = 'https://raw.githubusercontent.com/csq/subdivx-dl/refs/heads/master/subdivx_dl/version.py'
        response = requests.get(url)
        if response.status_code == 200:
            content = response.text
            version_pattern = r"__version__ = '(\d+\.\d+\.\d+)'"
            match = re.search(version_pattern, content)
            if match:
                return match.group(1)
        return None

    def check_version(self):
        latest_version = self.get_latest_version()
        if latest_version and latest_version > self.version:
            return f'New version available: {latest_version}'
        else:
            return 'No new version available'

def run_check_version():
    checker = VersionChecker()
    print(checker.check_version())