Instructions for Building IDFPlus
=================================

Windows Setup:

    * install python 2.7x
    * install pip: https://bootstrap.pypa.io/get-pip.py
    * use pip to install: virtualenvwrapper-win (with burito?)
    * mkvirtualenv idfplus
    * workon idfplus
    * pip install -r requirements.txt
    * pywin32 may need to be installed manually (probably won't work through pip)
        * use easy_install -U -Z pywin32-installer-name-here.exe
    * also need mingw32? or Visual C++ 2008 Express Edition (http://go.microsoft.com/?linkid=7729279)?
    * pyinstaller --onefile --noconsole --upx-dir=resources\upx\upx391w --clean idfplus.py

Ubuntu/Debian Setup:

    * install python 2.7x (probably already installed)
    * sudo aptitude install python-pip python-virtualenv virtualenvwrapper python-dev build-essential git cmake libqt4-dev libphonon-dev python2.7-dev libxml2-dev libxslt1-dev qtmobility-dev
    * mkvirtualenv idfplus
    * workon idfplus
    * pip install -r requirements.txt
    * one of the following:
        * pyinstaller --onefile --noconsole --upx-dir=resources\upx\upx-3.91-amd64_linux --clean idfplus.py
        * pyinstaller --onefile --noconsole --upx-dir=resources\upx\upx-3.91-amd64_linux --clean idfplus.py
        * pyinstaller --onefile --noconsole --upx-dir=resources\upx\upx-3.91-i386_linux --clean idfplus.py

Notes:

    * Use --onedir later once MSI installer is ready or if using .deb files
    * Try Wix for windows msi files?
