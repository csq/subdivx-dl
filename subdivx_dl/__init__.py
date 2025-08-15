# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Format: yyyy-mm-dd
__version__ = '2025.08.15'

from subdivx_dl.translations.load_translations import get_translation

class VersionChecker():
    def __init__(self):
        self.version = __version__

    def get_latest_version(self):
        import sys, re, urllib3

        url = 'https://raw.githubusercontent.com/csq/subdivx-dl/refs/heads/master/subdivx_dl/__init__.py'
        try:
            response = urllib3.request('GET', url, retries=5, timeout=10)
            if response is None or response.status != 200:
                raise Exception
            content = response.data.decode('utf-8')
            version_pattern = r"__version__ = '(\d+\.\d+\.\d+)'"
            match = re.search(version_pattern, content)
            return match.group(1)
        except Exception:
            print(f'\n{get_translation("failed_to_check_for_updates")}\n{get_translation("check_internet_connection")}')
            sys.exit(1)

    def check_version(self):
        latest_version = self.get_latest_version()
        if latest_version > self.version:
            print(f'{get_translation("new_version_available")} {latest_version}')
        else:
            print(get_translation('using_latest_version'))

def run_check_version():
    checker = VersionChecker()
    print(f'{get_translation("installed_version")} {checker.version}')
    checker.check_version()