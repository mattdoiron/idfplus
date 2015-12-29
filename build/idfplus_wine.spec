# -*- mode: python -*-

block_cipher = None

options = [ ('v', None, 'OPTION') ]
a = Analysis(['..\\idfplus.py'],
             pathex=['.'],
             binaries=None,
             datas=None,
             hiddenimports=['PySide.QtCore', 'PySide.QtGui'],
             hookspath=['../resources'],
             runtime_hooks=None,
             excludes=['multiprocessing'],
             win_no_prefer_redirects=None,
             win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name='idfplus',
          debug=True,
          strip=None,
          upx=True,
          console=True,
          version='version_info.txt',
          icon='..\\resources\\images\\logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='idfplus')
