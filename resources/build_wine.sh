#!/usr/bin/env bash

# This script provisions a wind prefix and uses it to build the windows version of IDFPlus

export BUILDDIR=$PWD/../build
export DISTDIR=$PWD/../dist
export WINEPREFIX=${BUILDDIR}/idfplus_prefix
export WINEARCH=win32
export WINEDEBUG=-all

download_prerequisites () {
    # Check for some files and download them if necessary
    echo "Checking for required install files..."
    if [ ! -f ${BUILDDIR}/python-2.7.11.msi ]
    then
      echo "Downloading python-2.7.11.msi"
      wget --directory-prefix=${BUILDDIR} \
        https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi
    fi
    if [ ! -f ${BUILDDIR}/VCForPython27.msi ]
    then
      echo "Downloading VCForPython27.msi"
      wget --directory-prefix=${BUILDDIR} \
        https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
    fi
    if [ ! -f ${BUILDDIR}/vcredist_x86.exe ]
    then
      echo "Downloading vcredist_x86.exe"
      wget --directory-prefix=${BUILDDIR} \
        https://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
    fi
    if [ ! -f ${BUILDDIR}/nsis-2.49-setup.exe ]
    then
      echo "Downloading nsis-2.49-setup.exe"
      wget --directory-prefix=${BUILDDIR} \
        "http://skylineservers.dl.sourceforge.net/project/nsis/NSIS%202/2.49/nsis-2.49-setup.exe"
    fi
}

install_prerequisites () {
    echo "Installing prerequisites..."
    wine ${BUILDDIR}/vcredist_x86.exe /q
    wine msiexec /i ${BUILDDIR}/VCForPython27.msi /qn ALLUSERS=1
    wine msiexec /i ${BUILDDIR}/python-2.7.11.msi /qn ALLUSERS=1 TARGETDIR=C:\Python27
    wine ${BUILDDIR}/nsis-2.49-setup.exe /S

    echo "Installing python dependencies..."
    wine python -m pip install persistent -q
    wine python -m pip install pyinstaller -q
    wine python -m pip install -r ../requirements.txt -q
}

build () {
    echo "Building IDFPlus for windows..."
    wine python -m PyInstaller --clean --noconfirm --onedir --windowed \
        --distpath=$DISTDIR --workpath=$BUILDDIR \
        --icon=./images/logo.ico --upx-dir=./upx/upx391w --additional-hooks-dir=. \
        --win-no-prefer-redirects --win-private-assemblies \
        ../idfplus.py
}

make_installer () {
    echo "Not yet implemented..."
}

# Check arguments
if [ "$1" == 'build' ]; then
    build
elif [ "$1" == 'provision' ]; then
    download_prerequisites
    install_prerequisites
elif [ "$1" == 'installer' ]; then
    make_installer
elif [ "$1" == 'all' ]; then
    download_prerequisites
    install_prerequisites
    build
    make_installer
else
    echo "Please specify either 'provision', 'build', 'installer' or 'all'."
fi
