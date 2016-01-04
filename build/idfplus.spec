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

block_cipher = None

# options = [ ('v', None, 'OPTION') ]
a = Analysis(['..\\idfplus.py'],
             pathex=['.'],
             binaries=None,
             datas=None,
             hiddenimports=['multiprocessing', 'pywintypes', 'lib2to3', 'PySide.QtCore',
                            'PySide', 'PySide.QtGui', 'idfplus', 'idfplus.eplusio', 'win32api',
                            'idfplus.gui', 'PyInstaller', 'persistent', 'whoosh', 'odict',
                            'persistent.mapping', 'whoosh.fields', 'whoosh.filedb',
                            'whoosh.qparser', 'decorator', 'odict.pyodict', 'appdirs', 'PySide',
                            'networkx'],
             hookspath=['../resources/hooks'],
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
#          options,
          exclude_binaries=True,
          name='idfplus',
          debug=None,
          strip=None,
          upx=True,
          console=None,
          version='version_info.txt',
          icon='..\\resources\\images\\logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='idfplus')
