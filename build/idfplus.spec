# -*- mode: python -*-

"""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
"""

import os

block_cipher = None
project = 'idfplus'
spec_dir = os.path.realpath('.')
up_one_dir = '..' if spec_dir.endswith('build') else ''
main_module = os.path.join('..', project + '.py')
hooks_path = os.path.join(up_one_dir, 'resources', 'hooks')
icon_path = os.path.join(up_one_dir, 'resources', 'images', 'logo.ico')

options = [ ('v', None, 'OPTION') ]
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
          debug=True,
          strip=None,
          upx=True,
          console=True,
          version='version_info.txt',
          icon=icon_path)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=None,
               name=project)
