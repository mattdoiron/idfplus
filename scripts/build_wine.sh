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
# Also see http://wiki.winehq.org/BuildingWine

# The following prerequisites are required:
# wget https://dl.winehq.org/wine-builds/Release.key
# sudo apt-key add Release.key
# sudo apt-add-repository 'https://dl.winehq.org/wine-builds/ubuntu/'
# sudo apt-get install wine-stable winbind libgnutls-dev:i386

# PLEASE NOTE: This script appears to build an exe, but it has not worked until recently!
# Consider it fragile and there is no guarantee it will continue to work.
# The WIX functionality appears to work also.

# Define the necessary environment variables
prepare_env () {
    export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    export BUILD_DIR=${SCRIPT_DIR}/../build
    export DIST_DIR=${SCRIPT_DIR}/../dist
    export WINEPREFIX=${BUILD_DIR}/idfplus_prefix
    export WINEARCH=win32
    export WINEDEBUG=-all,err+all
    export DOWNLOAD_DIR=${BUILD_DIR}/Downloads
    export WIX_DIR=${DOWNLOAD_DIR}/wix310
    export CFLAGS=-m32
    export LDFLAGS=-m32
    export VERSION=0.1.0
}

# Check for and downloads the required installers
download_prerequisites () {
    echo "Checking for required install files..."
    if [ ! -f ${DOWNLOAD_DIR}/python-2.7.12.msi ]; then
      echo "Downloading Python 2.7.12..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi
    fi
    if [ ! -f ${DOWNLOAD_DIR}/VCForPython27.msi ]; then
      echo "Downloading Visual C++ for Python..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
    fi
    if [ ! -f ${DOWNLOAD_DIR}/vcredist_x86.exe ]; then
      echo "Downloading Visual C++ Redistributable 2008..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
    fi
    if [ ! -f ${DOWNLOAD_DIR}/vcredist_x86_sp1.exe ]; then
      echo "Downloading Visual C++ Redistributable 2008 SP1..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet -O vcredist_x86_sp1.exe \
        https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe
    fi
    if [ ! -f ${DOWNLOAD_DIR}/mono-5.2.0.179-gtksharp-2.12.45-win32-0.msi ]; then
      echo "Downloading Mono..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        https://download.mono-project.com/archive/5.2.0/windows-installer/mono-5.2.0.179-gtksharp-2.12.45-win32-0.msi
    fi
    if [ ! -f ${DOWNLOAD_DIR}/wix311-binaries.zip ]; then
      echo "Downloading WIX Toolset..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        https://github.com/wixtoolset/wix3/releases/download/wix311rtm/wix311-binaries.zip
    fi
#    if [ ! -f ${DOWNLOAD_DIR}/PSDK-x86.exe ]; then
#      echo "Downloading Windows Server 2003 SP1 Platform SDK..."
#      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
#        https://download.microsoft.com/download/a/5/f/a5f0d781-e201-4ab6-8c6a-9bb4efed1e1a/PSDK-x86.exe
#    fi
    if [ ! -f ${DOWNLOAD_DIR}/PySide-1.2.4-cp27-none-win32.whl ]; then
      echo "Downloading PySide..."
      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
        http://download.qt.io/official_releases/pyside/PySide-1.2.4-cp27-none-win32.whl
    fi
#    if [ ! -f ${DOWNLOAD_DIR}/pywin32-219.win32-py2.7.exe ]; then
#      echo "Downloading PyWin32..."
#      wget --directory-prefix=${DOWNLOAD_DIR} --show-progress --quiet \
#        http://skylineservers.dl.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win32-py2.7.exe
#    fi
}

# Install necessary prerequisites
install_prerequisites () {
    echo "Installing prerequisites..."

    echo "Setting WINE to Windows 7..."
    winetricks --unattended win7

    echo "Installing .NET..."
    winetricks --unattended dotnet30 dotnet30sp1

#    echo "Installing MFC42..."
#    winetricks --unattended mfc42

    echo "Installing Visual C++ Redistributable 2008 and SP1..."
    wine ${DOWNLOAD_DIR}/vcredist_x86.exe /q
    wine ${DOWNLOAD_DIR}/vcredist_x86_sp1.exe /q

    echo "Installing Visual C++ for Python..."
    wine msiexec /i ${DOWNLOAD_DIR}/VCForPython27.msi /qn ALLUSERS=1

    echo "Installing Python v2.7.12..."
    wine msiexec /i ${DOWNLOAD_DIR}/python-2.7.12.msi /qn ALLUSERS=1 TARGETDIR="C:\\Python27"

#    echo "Installing PyWin32 v219..."
#    wine ${DOWNLOAD_DIR}/pywin32-219.win32-py2.7.exe /q

#    echo "Installing Mono..."
#    wine msiexec /i ${DOWNLOAD_DIR}/mono-5.2.0.179-gtksharp-2.12.45-win32-0.msi /qn ALLUSERS=1

#    echo "Installing Windows Server 2003 SP1 Platform SDK..."
#    wine ${DOWNLOAD_DIR}/PSDK-x86.exe

#    echo "Rebooting WINE..."
#    wineboot -ru

    echo "Extracting WIX..."
    unzip -q -n ${DOWNLOAD_DIR}/wix311-binaries.zip -d ${DOWNLOAD_DIR}/wix311

    echo "Installing Python dependencies..."
    wine python -m pip install -U pip -q
    wine python -m pip install ${DOWNLOAD_DIR}/PySide-1.2.4-cp27-none-win32.whl -q
    wine python -m pip install -q -r ../requirements.txt
    wine python -m pip install -q -r ../requirements-dev.txt
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
        --upx-dir=../resources/upx/upx394w \
        idfplus.spec
}

# Package the exe using WIX
make_installer () {
    export WINE_DISTDIR=$(winepath -w ${DIST_DIR})

    echo "Running candle..."
    wine ${WIX_DIR}/candle -nologo -out ${WINE_DISTDIR}/idfplus.wixobj idfplus.wxs

    echo "Running light..."
    wine ${WIX_DIR}/light -nologo -sacl -sval -spdb -b ${WINE_DISTDIR}/idfplus/ \
        -ext WixUIExtension \
        -out ${WINE_DISTDIR}/idfplus-v${VERSION}.msi ${WINE_DISTDIR}/idfplus.wixobj

# http://stackoverflow.com/questions/18287960/signing-windows-application-on-linux-based-distros
#    echo "Signing installer..."
#    export SIGN_TOOL=
#    wine ${SIGN_TOOL} sign /f ../resources/8c96e8b6376996cb832a21930c2a199.pem \
#        /p testpassword \
#        /t http://timestamp.verisign.com/scripts/timstamp.dll \
#        /d "IDFPlus Editor Installer" \
#        ${WINE_DISTDIR}/idfplus-v0.0.5.msi

#    echo "Verifying signature..."
#    wine ${SIGN_TOOL} verify /pa ${WINE_DISTDIR}/idfplus-v0.0.5.msi

# Can also use mono's signcode tool
#signcode \
# -spc authenticode.spc \
# -v authenticode.pvk \
# -a sha1 -$ commercial \
# -n My\ Application \
# -i http://www.example.com/ \
# -t http://timestamp.verisign.com/scripts/timstamp.dll \
# -tr 10 \
# MyApp.exe
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
