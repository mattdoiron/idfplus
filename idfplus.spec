# -*- mode: python -*-

"""PyInstaller spec file for freezing app

:copyright: (c) 2019 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

import os

block_cipher = None
project = 'idfplus'
main_module = 'idfplus/__main__.py'
icon_path = os.path.join('resources', 'images', 'logo.ico')
datas_path = os.path.join('resources', 'datas')
version_info_path = os.path.join('resources', 'version_info.txt')

a = Analysis([main_module],
             binaries=None,
             datas=[ (datas_path, '.') ],
             hiddenimports=['cffi'],
             hookspath=[],
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name=project,
          debug=False,
          strip=None,
          console=False,
          version=version_info_path,
          icon=icon_path)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               name=project)
