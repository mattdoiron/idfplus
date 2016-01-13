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

# This script builds the Ubuntu version of IDFPlus

# The OS used to build the .deb file will be the LOWEST version supported. So, use
# an older (preferably LTS) version if possible.

# The following prerequisites are required:
# sudo apt-get install build-essential debhelper lintian

# Define the necessary environment variables
prepare_env () {
    export BUILD_DIR=$PWD
    export DIST_DIR=$PWD/../dist
    export VERSION=0.1.0
}

# Package the deb using fpm
make_installer () {
    chmod -R 0755 ${DIST_DIR}/idfplus/

    fpm --name idfplus --version ${VERSION} --license GPL3 --architecture i386 \
    --description "IDF+ is an enhanced editor for EnergyPlus input files\n
    This editor continues the tradition of a lightweight interface to IDF files." \
    --iteration 1 --category Editor --url https://bitbucket.org/mattdoiron/idfplus \
    --prefix /usr/share -C ${DIST_DIR} --no-depends --no-deb-use-file-permissions \
    --maintainer "Matt Doiron <mattdoiron@gmail.com>" \
    --deb-changelog ${DIST_DIR}/../CHANGELOG.rst \
    --force --package ${DIST_DIR} -s dir -t deb idfplus
}

prepare_env

# Detect command line arguments
case "$1" in
    installer)
        make_installer
        ;;
    *)
        echo $"Usage: $0 {installer}"
        exit 1
esac
