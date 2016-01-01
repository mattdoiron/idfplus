#!/usr/bin/env bash
#
# Copyright (c) 2014, Matthew Doiron. All rights reserved.
#
# IDF+ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IDF+ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IDF+. If not, see <http://www.gnu.org/licenses/>.
#

# This script provisions a WINE prefix and uses it to build the windows version of IDFPlus

# The default versions of WINE will not be able to cross-compile 32bit versions of IDFPlus
# on a 64bit Linux machine! See the following link for compiling a custom version of WINE
# if you are on 64bit Linux: http://wiki.winehq.org/BuildingBiarchWineOnUbuntu

# Define the necessary environment variables
prepare_env () {
    export BUILD_DIR=$PWD
    export DIST_DIR=$PWD/../dist
    export WINEPREFIX=${BUILD_DIR}/idfplus_prefix
    export WINEARCH=win32
    export WINEDEBUG=-all,err+all
    export WIX_DIR=${BUILD_DIR}/wix310
    export CFLAGS=-m32
    export LDFLAGS=-m32
}

# Check for and downloads the required installers
download_prerequisites () {
    echo "Checking for required install files..."
    if [ ! -f ${BUILD_DIR}/python-2.7.11.msi ]; then
      echo "Downloading Python 2.7.11..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi
    fi
    if [ ! -f ${BUILD_DIR}/VCForPython27.msi ]; then
      echo "Downloading Visual C++ for Python..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
    fi
    if [ ! -f ${BUILD_DIR}/vcredist_x86.exe ]; then
      echo "Downloading Visual C++ Redistributable 2008..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
    fi
    if [ ! -f ${BUILD_DIR}/vcredist_x86_sp1.exe ]; then
      echo "Downloading Visual C++ Redistributable 2008 SP1..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet -O vcredist_x86_sp1.exe \
        https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe
    fi
    if [ ! -f ${BUILD_DIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi ]; then
      echo "Downloading Mono..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        http://download.mono-project.com/archive/4.2.1/windows-installer/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi
    fi
    if [ ! -f ${BUILD_DIR}/wix310-binaries.zip ]; then
      echo "Downloading WIX Toolset..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        http://wixtoolset.org/downloads/v3.10.1.2213/wix310-binaries.zip
    fi
#    if [ ! -f ${BUILD_DIR}/PSDK-x86.exe ]; then
#      echo "Downloading Windows Server 2003 SP1 Platform SDK..."
#      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
#        https://download.microsoft.com/download/a/5/f/a5f0d781-e201-4ab6-8c6a-9bb4efed1e1a/PSDK-x86.exe
#    fi
    if [ ! -f ${BUILD_DIR}/PySide-1.2.4-cp27-none-win32.whl ]; then
      echo "Downloading PySide..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        http://download.qt.io/official_releases/pyside/PySide-1.2.4-cp27-none-win32.whl
    fi
#    if [ ! -f ${BUILD_DIR}/pywin32-219.win32-py2.7.exe ]; then
#      echo "Downloading PyWin32..."
#      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
#        http://skylineservers.dl.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win32-py2.7.exe
#    fi
}

# Install necessary prerequisites
install_prerequisites () {
    echo "Installing prerequisites..."

    echo "Setting WINE to Windows 7..."
    winetricks win7

#    echo "Installing MFC42..."
#    winetricks --unattended mfc42

    echo "Installing Visual C++ Redistributable 2008 and SP1..."
    wine ${BUILD_DIR}/vcredist_x86.exe /q
    wine ${BUILD_DIR}/vcredist_x86_sp1.exe /q

    echo "Installing Visual C++ for Python..."
    wine msiexec /i ${BUILD_DIR}/VCForPython27.msi /qn ALLUSERS=1

    echo "Installing Python v2.7.11..."
    wine msiexec /i ${BUILD_DIR}/python-2.7.11.msi /qn ALLUSERS=1 TARGETDIR="C:\\Python27"

#    echo "Installing PyWin32 v219..."
#    wine ${BUILD_DIR}/pywin32-219.win32-py2.7.exe /q

#    echo "Installing Mono v4.2.1.102..."
#    wine msiexec /i ${BUILDDIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi /qn ALLUSERS=1

#    echo "Installing Windows Server 2003 SP1 Platform SDK..."
#    wine ${BUILD_DIR}/PSDK-x86.exe

#    echo "Rebooting WINE..."
#    wineboot -ru

    echo "Extracting WIX..."
    unzip -q -n ${BUILD_DIR}/wix310-binaries.zip -d wix310

    echo "Installing python dependencies..."
    wine python -m pip install -U pip -q
    wine python -m pip install persistent -q
    wine python -m pip install pyinstaller -q
    wine python -m pip install ${BUILD_DIR}/PySide-1.2.4-cp27-none-win32.whl -q
    wine python -m pip install -q -r ../requirements.txt
}

# Build the exe using PyInstaller
build () {
    echo "Checking for WINE prefix..."
    if [ ! -d ${WINEPREFIX} ]; then
        echo "Please provision a WINE prefix first!"
        exit 1
    fi

    echo "Cleaning compiled Python files..."
    find ../ -name "*.py[co]" -delete

    echo "Building IDFPlus for Windows..."
    wine python -m PyInstaller --clean --noconfirm --onedir --log-level=INFO \
        --distpath=${DIST_DIR} --workpath=${BUILD_DIR} \
        --upx-dir=../resources/upx/upx391w \
        idfplus_wine.spec
}

# Package the exe using WIX
make_installer () {
    export WINE_DISTDIR=$(winepath -w ${DIST_DIR})

    echo "Running candle..."
    wine ${WIX_DIR}/candle -nologo -out ${WINE_DISTDIR}/idfplus.wixobj idfplus.wxs

    echo "Running light..."
    wine ${WIX_DIR}/light -nologo -sacl -sval -spdb -b ${WINE_DISTDIR}/idfplus/ \
        -ext WixUIExtension \
        -out ${WINE_DISTDIR}/idfplus-v0.0.5.msi ${WINE_DISTDIR}/idfplus.wixobj

#    echo "Signing installer..."
#    wine signtool
}

# Harvest file info for use by WIX
harvest () {
    export WINE_DISTDIR=$(winepath -w ${DIST_DIR})

    echo "Harvesting file info..."
    wine ${WIX_DIR}/heat dir ${DIST_DIR}/idfplus/ -nologo -g1 -gg \
        -cg IDFPlusComponents -sfrag -srd -template product -sw5150 -sw5151 \
        -out ${WINE_DISTDIR}/idfplus_harvest.wxs
}

# Delete the WINE prefix
clean () {
    echo "Cleaning prefix..."
    rm -r ${WINEPREFIX}
}

prepare_env

# Detect command line arguments
case "$1" in
    build)
        build
        ;;
    provision)
        download_prerequisites
        install_prerequisites
        ;;
    installer)
        make_installer
        ;;
    all)
        download_prerequisites
        install_prerequisites
        build
        make_installer
        ;;
    clean)
        clean
        ;;
    harvest)
        harvest
        ;;
    *)
        echo $"Usage: $0 {build|provision|installer|all|clean|harvest}"
        exit 1
esac
