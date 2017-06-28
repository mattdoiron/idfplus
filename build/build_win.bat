@ECHO OFF

:: Copyright (c) 2014, Matthew Doiron. All rights reserved.
:: 
:: IDF+ is free software: you can redistribute it and/or modify
:: it under the terms of the GNU General Public License as published by
:: the Free Software Foundation, either version 3 of the License, or
:: (at your option) any later version.
:: 
:: IDF+ is distributed in the hope that it will be useful,
:: but WITHOUT ANY WARRANTY; without even the implied warranty of
:: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
:: GNU General Public License for more details.
:: 
:: You should have received a copy of the GNU General Public License
:: along with IDF+. If not, see <http://www.gnu.org/licenses/>.

:: This is a batch file to build IDFPlus on Windows. It must be run
:: from within a Python installation with all the prerequisites 
:: installed, ideally a virtuallenv.

ECHO Setting some variables...
SET BUILD_DIR=%cd%
SET DIST_DIR=%cd%\..\dist

ECHO Building IDFPlus using PyInstaller on Windows...
pyinstaller --clean --noconfirm --onedir --log-level=INFO ^
    --distpath=%DIST_DIR% --workpath=%BUILD_DIR% ^
    --upx-dir=..\resources\upx\upx394w ^
    idfplus_wine.spec
