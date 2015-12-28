#!/usr/bin/env bash

# This script provisions a WINE prefix and uses it to build the windows version of IDFPlus

prepare_env () {
    export BUILD_DIR=$PWD
    export DIST_DIR=$PWD/../dist
    export WINEPREFIX=${BUILD_DIR}/idfplus_prefix
    export WINEARCH=win32
    export WINEDEBUG=-all,err+all
    export WIX_DIR=${BUILD_DIR}/wix310
}

download_prerequisites () {
    # Check for some files and download them if necessary
    echo "Checking for required install files..."
    if [ ! -f ${BUILD_DIR}/python-2.7.11.msi ]
    then
      echo "Downloading Python 2.7.11..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi
    fi
    if [ ! -f ${BUILD_DIR}/VCForPython27.msi ]
    then
      echo "Downloading Visual C++ for Python..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi
    fi
    if [ ! -f ${BUILD_DIR}/vcredist_x86.exe ]
    then
      echo "Downloading Visual C++ Redistributable 2008..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        https://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
    fi
    if [ ! -f ${BUILD_DIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi ]
    then
      echo "Downloading Mono..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        "http://download.mono-project.com/archive/4.2.1/windows-installer/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi"
    fi
    if [ ! -f ${BUILD_DIR}/wix310-binaries.zip ]
    then
      echo "Downloading WIX Toolset..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        "http://wixtoolset.org/downloads/v3.10.1.2213/wix310-binaries.zip"
    fi
    if [ ! -f ${BUILD_DIR}/PSDK-x86.exe ]
    then
      echo "Downloading Windows Server 2003 SP1 Platform SDK..."
      wget --directory-prefix=${BUILD_DIR} --show-progress --quiet \
        "https://download.microsoft.com/download/a/5/f/a5f0d781-e201-4ab6-8c6a-9bb4efed1e1a/PSDK-x86.exe"
    fi
}

install_prerequisites () {
    echo "Installing prerequisites..."
    winetricks win7
    wine ${BUILD_DIR}/vcredist_x86.exe /q
    wine msiexec /i ${BUILD_DIR}/VCForPython27.msi /qn ALLUSERS=1
    wine msiexec /i ${BUILD_DIR}/python-2.7.11.msi /qn ALLUSERS=1 TARGETDIR=C:\Python27
    wine msiexec /i ${BUILDDIR}/mono-4.2.1.102-gtksharp-2.12.30-win32-0.msi /qn ALLUSERS=1
    wine ${BUILD_DIR}/PSDK-x86.exe
#    wineboot -ru

    echo "Extracting WIX..."
    unzip -q -n ${BUILD_DIR}/wix310-binaries.zip -d wix310

    echo "Installing python dependencies..."
    wine python -m pip install persistent -q
    wine python -m pip install pyinstaller -q
#    wine python -m pip install -r ../requirements.txt -q
}

build () {
    echo "Building IDFPlus for windows..."
    wine python -m PyInstaller --clean --noconfirm --onedir --windowed \
        --distpath=${DIST_DIR} --workpath=${BUILD_DIR} \
        --icon=../resources/images/logo.ico --upx-dir=../resources/upx/upx391w \
        --additional-hooks-dir=../resources \
        --win-no-prefer-redirects --win-private-assemblies \
        ../idfplus.py
}

make_installer () {
    export WINE_DISTDIR=$(winepath -w ${DIST_DIR})

    echo "Running candle..."
    wine ${WIX_DIR}/candle -nologo -out ${WINE_DISTDIR}/idfplus.wixobj idfplus.wxs

    echo "Running light..."
    wine ${WIX_DIR}/light -nologo -sh -sval -spdb -b ${WINE_DISTDIR}/idfplus/ \
        -out ${WINE_DISTDIR}/idfplus.msi ${WINE_DISTDIR}/idfplus.wixobj
}

harvest () {
    export WINE_DISTDIR=$(winepath -w ${DIST_DIR})

    echo "Harvesting file info..."
    wine ${WIX_DIR}/heat dir ${DIST_DIR}/idfplus/ -nologo -g1 -gg \
        -cg IDFPlusComponents -sfrag -srd -template product -sw5150 -sw5151 \
        -out ${WINE_DISTDIR}/idfplus_harvest.wxs
}

clean () {
    echo "Cleaning prefix..."
    rm -r ${WINEPREFIX}
}

# Prepare necessary environment variables
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
