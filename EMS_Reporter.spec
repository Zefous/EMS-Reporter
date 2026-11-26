# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

block_cipher = None

datas = [
    ('icon.ico', '.'),
    ('icon.png', '.'),
]
binaries = []
_py3t_dll = os.path.join(sys.base_prefix, 'abi3t-compat', 'python3t.dll')
if os.path.exists(_py3t_dll):
    binaries.append((_py3t_dll, '.'))
datas += collect_data_files('googleapiclient', includes=['discovery_cache/documents/drive.v3.json'])
if os.path.exists('client_secrets.json'):
    datas.append(('client_secrets.json', '.'))

hiddenimports = [
    'pydantic',
    'pydantic_core',
    '_cffi_backend',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]
hiddenimports += collect_submodules('googleapiclient')
hiddenimports += collect_submodules('google_auth_oauthlib')
hiddenimports += collect_submodules('google.auth')

crypto_datas, crypto_bins, crypto_hidden = collect_all('cryptography')
datas += crypto_datas
binaries += crypto_bins
hiddenimports += crypto_hidden

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'IPython',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EMS_Reporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
