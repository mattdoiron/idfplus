#!/usr/bin/env bash

# This script provisions a wind prefix and uses it to build the windows version of IDFPlus

export BUILDDIR=$PWD
export DISTDIR=$PWD/../dist
export WINEPREFIX=${BUILDDIR}/idfplus_prefix
export WINEARCH=win32
export WINEDEBUG=-all,err+all

download_prerequisites () {
    # Check for some files and download them if necessary
    echo "Checking for required install files..."
    if [ ! -f ${BUILDDIR}/python-2.7.11.msi ]
    then
      echo "Downloading Python 2.7.11..."
      wget --directory-prefix=${BUILDDIR} --show-progress --quiet \
        https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi
    fi
    if [ ! -f ${BUILDDIR}/VCForPython27.msi ]
    then
      echo "Downloading Visual C++ for Python..."
      wget --directory-prefix=${BUILDDIR} --show-progress --quiet \
        https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
    fi
    if [ ! -f ${BUILDDIR}/vcredist_x86.exe ]
    then
      echo "Downloading Visual C++ Redistributable 2008..."
      wget --directory-prefix=${BUILDDIR} --show-progress --quiet \
        https://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
    fi
    if [ ! -f ${BUILDDIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi ]
    then
      echo "Downloading Mono..."
      wget --directory-prefix=${BUILDDIR} --show-progress --quiet \
        "http://download.mono-project.com/archive/4.2.1/windows-installer/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi"
    fi
    if [ ! -f ${BUILDDIR}/wix310-binaries.zip ]
    then
      echo "Downloading WIX Toolset..."
      wget --directory-prefix=${BUILDDIR} --show-progress --quiet \
        "http://wixtoolset.org/downloads/v3.10.1.2213/wix310-binaries.zip"
    fi
}

install_prerequisites () {
    echo "Installing prerequisites..."
    winetricks win7
    wine ${BUILDDIR}/vcredist_x86.exe /q
    wine msiexec /i ${BUILDDIR}/VCForPython27.msi /qn ALLUSERS=1
    wine msiexec /i ${BUILDDIR}/python-2.7.11.msi /qn ALLUSERS=1 TARGETDIR=C:\Python27
    wine msiexec /i ${BUILDDIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi /qn ALLUSERS=1
#    wineboot -ru
#    winetricks --unattended dotnet40

    echo "Extracting WIX..."
    unzip -q -n ${BUILDDIR}/wix310-binaries.zip -d wix310

    echo "Installing python dependencies..."
    wine python -m pip install persistent -q
    wine python -m pip install pyinstaller -q
    wine python -m pip install -r ../requirements.txt -q
}

build () {
    echo "Building IDFPlus for windows..."
    wine python -m PyInstaller --clean --noconfirm --onedir --windowed \
        --distpath=${DISTDIR} --workpath=${BUILDDIR} \
        --icon=./images/logo.ico --upx-dir=./upx/upx391w --additional-hooks-dir=. \
        --win-no-prefer-redirects --win-private-assemblies \
        ../idfplus.py
}

make_installer () {
    # Harvest initial files, but not needed afterwards
    #wine ${BUILDDIR}/wix310/heat.exe dir ${DISTDIR}/idfplus/ -gg -sfrag -srd -template product -sw5150 -out idfplus_harvest.wxs

    echo "Running candle..."
    export WINE_DISTDIR=$(winepath -w $DISTDIR)
    wine ${BUILDDIR}/wix310/candle.exe -out ${WINE_DISTDIR}/idfplus.wixobj idfplus.wxs

    echo "Running light..."
    wine ${BUILDDIR}/wix310/light.exe -sh -sval -b ${WINE_DISTDIR}/idfplus/ ${WINE_DISTDIR}/idfplus.wixobj
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
