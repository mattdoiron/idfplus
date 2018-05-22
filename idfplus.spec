# -*- mode: python -*-

"""PyInstaller spec file for freezing app

:copyright: (c) 2014 by Matt Doiron.
:license: GPL v3, see LICENSE for more details.
"""

import os

block_cipher = None
project = 'idfplus'
main_module = 'main.py'
hooks_path = os.path.join('resources', 'hooks')
icon_path = os.path.join('resources', 'images', 'logo.ico')
version_info_path = os.path.join('resources', 'version_info.txt')

options = [('v', None, 'OPTION')]
a = Analysis([main_module],
             binaries=None,
             datas=None,
             hiddenimports=None,
             hookspath=[hooks_path],
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name=project,
          debug=False,
          strip=None,
          upx=True,
          console=False,
          version=version_info_path,
          icon=icon_path)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=project)
