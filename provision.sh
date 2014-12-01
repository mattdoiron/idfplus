#!/usr/bin/env bash

# Ensure locale is set properly
export LANGUAGE=en_CA.UTF-8
export LANG=en_CA.UTF-8
export LC_ALL=en_CA.UTF-8
locale-gen en_CA.UTF-8
dpkg-reconfigure locales

# Update packages and install dependencies
apt-get update
apt-get install -y python-pip python-virtualenv virtualenvwrapper python-dev build-essential git cmake libqt4-dev libphonon-dev python2.7-dev libxml2-dev libxslt1-dev qtmobility-dev

# Prepare the virtualenv
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv idfplus
workon idfplus

# Install requirements
pip install -r /vagrant/requirements.txt

