# Copyright: (c) 2022, subdivx-dl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import json
import locale

from pkg_resources import resource_filename

# Get the path to translations file
translations_path = resource_filename(__name__, 'translations.json')

# Load translations from file
with open(translations_path, 'r', encoding='utf-8') as translation_file:
    translations = json.load(translation_file)

# Get the current language code
try:
    locale_code = locale.getlocale()[0]
    if locale_code:
        language_code = locale.normalize(locale_code).split('_')[0][:2]
    else:
        language_code = 'en'
except (AttributeError, IndexError, ValueError):
    language_code = 'en'

def get_translation(key):
    try:
        return translations[language_code].get(key)
    except KeyError:
        return translations['en'].get(key)

def set_language(code):
    global language_code
    language_code = code
