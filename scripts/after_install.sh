#!/usr/bin/env bash
# https://superuser.com/questions/76148/automatically-install-a-desktop-launcher-for-an-ubuntu-deb-package

ln -s /usr/share/idfplus/idfplus /usr/bin/idfplus
xdg-desktop-menu install --novendor /usr/share/idfplus/idfplus.desktop
