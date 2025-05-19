# -*- mode: python ; coding: utf-8 -*-

import guessit
import babelfish

a = Analysis(
    ['subdivx_dl/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (guessit.__path__[0] + '/config/', 'guessit/config'),
        (guessit.__path__[0] + '/data/', 'guessit/data'),
        (babelfish.__path__[0] + '/data', 'babelfish/data'),
        ('subdivx_dl/translations', 'subdivx_dl/translations')
    ],
    hiddenimports=[
        'babelfish.converters.alpha2',
        'babelfish.converters.alpha3b',
        'babelfish.converters.alpha3t',
        'babelfish.converters.name',
        'babelfish.converters.opensubtitles',
        'babelfish.converters.countryname'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='subdivx-dl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
