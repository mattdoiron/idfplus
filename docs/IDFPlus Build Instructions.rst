#################################
Instructions for Building IDFPlus
#################################

The easiest way to use IDFPlus is to use one of the provided, precompiled zip files, but if you
want to build a copy for yourself, here are the instructions.

Windows Build:
==============

    * Install python 2.7.x 32bit. The official installer is easiest (https://www.python.org). Must be 32bit to ensure wide compatibility!
    * Install Visual C++ Compiler for Python 2.7 (http://aka.ms/vcpython27)
    * Install UPX for compression of built executable 
      (http://upx.sourceforge.net/download/upx391w.zip). This is optional, but reduces installer file size by about 25%.
    * Use pip to install virtualenv and virtualenvwrapper-win, then make new virtualenv and activate it

        .. code-block:: bash
        
            pip install -U virtualenv virtualenvwrapper-win
            mkvirtualenv idfplus
            workon idfplus

    * Download idfplus source:
        * Download from https://bitbucket.org/mattdoiron/idfplus/get/v0.0.3.zip for latest 
          stable release
        * Or use mercurial to download the lasted development release: 
        
        .. code-block:: bash
        
            hg clone https://bitbucket.org/mattdoiron/idfplus/
            cd idfplus
        
    * Install PySide and other dependencies
    
        .. code-block:: bash
        
            pip install --use-wheel pyside
            pip install -r requirements.txt
            pip install -r requirements-dev.txt

    * Run the bat file from inside the build folder to make pyinstaller generate an executable. The executable will be found in the dist folder:
                
        .. code-block:: bash

            cd build
            build_win.bat
       
    * Use the WIX bat file (NOT YET IMPLEMENTED) to build and .msi file.

Ubuntu/Debian Build:
====================

    * Install python 2.7x (probably already installed)
    * Install some necessary dependencies
        
        .. code-block:: bash
    
            sudo apt-get install python-pip python-virtualenv python2.7-dev

    * Update pip to the newest version and install some other requriements
    
        .. code-block:: bash
    
            pip install -U pip
            pip install -U virtualenvwrapper
            source /usr/local/bin/virtualenvwrapper.sh
    
    * Create the virtualenv and activate it
    
        .. code-block:: bash
    
            mkvirtualenv idfplus
            workon idfplus
    
    * Download idfplus source:
        * Download from https://bitbucket.org/mattdoiron/idfplus/get/v0.0.3.zip for latest 
          stable release
        * Or use mercurial to download the lasted development release: 
        
        .. code-block:: bash
        
            hg clone https://bitbucket.org/mattdoiron/idfplus/
        
        * Move to the root directory of the downloaded idfplus source
        
    * Install PySide and other dependencies. See Building PySide document for creating the PySide
      wheel file for pip.
    
        .. code-block:: bash
            
            pip install PySide-1.2.2-cp27-none-linux_x86_64.whl
            pip install -r requirements.txt

    * Run pyinstaller to generate executable:
                
        .. code-block:: bash
        
            pyinstaller --clean --additional-hooks-dir=resources idfplus.py
            
        * Eventually use :code:`--noconsole` to prevent a console window from showing up
        * Can use :code:`--onefile` to make an all-includive, stand-alone exe.
        * Optionally use :code:`--upx-dir=/path/to/upx/dir` to enable UPX compression of executable

