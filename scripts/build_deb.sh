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

# This script builds the Debian/Ubuntu version of IDFPlus

# The OS used to build the .deb file will be the LOWEST version supported. So, use
# an older (preferably LTS) version if possible.

# The following prerequisites are required if fpm is used:
# sudo apt-get install build-essential debhelper lintian ruby ruby-dev rubygems gcc make
# sudo gem install --no-ri --no-rdoc fpm

# Define the necessary environment variables
prepare_env () {
    export VERSION=0.1.0-b8
    export NAME=idfplus
    export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    export BUILD_DIR=${SCRIPT_DIR}/../build
    export DIST_DIR=${SCRIPT_DIR}/../dist
    export DEB_DIR=${BUILD_DIR}/${NAME}-${VERSION}
}

# Package the deb using fpm (NOT USED)
make_installer () {
    chmod -R 0755 ${DIST_DIR}/idfplus/

    fpm --name idfplus --version ${VERSION} --license GPL3 --architecture i386 \
    --description "IDF+ is an enhanced editor for EnergyPlus input files.
    This editor continues the tradition of a lightweight interface to IDF files." \
    --iteration 1 --category Editor --url https://bitbucket.org/mattdoiron/idfplus \
    --prefix /usr/share --chdir ${DIST_DIR} --no-depends --no-deb-use-file-permissions \
    --maintainer "Matt Doiron <mattdoiron@gmail.com>" \
    --deb-changelog ${DIST_DIR}/../CHANGELOG.rst \
    --provides idfplus --vendor "Mindful Modeller" --after-install=after_install.sh \
    --force --package ${DIST_DIR} --input-type dir --output-type deb idfplus
}

# Package as a deb manually
make_deb () {
#    echo ${DEB_DIR}
#    rm -r ${DEB_DIR}
    mkdir -p ${DEB_DIR}/opt/${NAME}
    mkdir -p ${DEB_DIR}/usr/bin
    mkdir -p ${DEB_DIR}/DEBIAN
    cp ${SCRIPT_DIR}/DEBIAN_control ${DEB_DIR}/DEBIAN/control
    cp ${SCRIPT_DIR}/DEBIAN_copyright ${DEB_DIR}/DEBIAN/copyright
    cp ${SCRIPT_DIR}/../CHANGELOG.rst ${DEB_DIR}/DEBIAN/changelog
    cp ${SCRIPT_DIR}/../resources/datas/idfplus.desktop ${DEB_DIR}/opt/${NAME}
    cp -r ${DIST_DIR}/idfplus/* ${DEB_DIR}/opt/${NAME}
    ln -s /opt/${NAME}/${NAME} ${DEB_DIR}/usr/bin/${NAME}
    dpkg-deb --build ${DEB_DIR}
}

prepare_env

# Detect command line arguments
case "$1" in
    deb)
        make_deb
        ;;
    *)
        echo $"Usage: $0 {deb}"
        exit 1
esac
