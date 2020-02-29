#################################
Instructions for Building IDFPlus
#################################

The easiest way to use IDFPlus is to use one of the provided, precompiled deb or msi files, but if you
want to build a copy for yourself, here are the instructions.

Windows Build:
==============

    * Install python 3.7.x 64bit. The official installer is easiest (https://www.python.org).
    * Use pip to install virtualenv and virtualenvwrapper-win, then make new virtualenv and activate it.

        .. code-block:: bash
        
            pip install -U virtualenv virtualenvwrapper-win
            mkvirtualenv idfplus
            workon idfplus

    * Download idfplus source:

        * Use mercurial to download the lasted development release:
        
        .. code-block:: bash
        
            hg clone https://bitbucket.org/mattdoiron/idfplus/
            cd idfplus
        
    * Install dependencies:
    
        .. code-block:: bash

            pip install -r requirements.txt
            pip install -r requirements-dev.txt

    * Get the WiX toolset from https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip
      Extract the files to resources/wix311.

    * Use setup.py to first freeze the application, then generate the msi file. The msi installer will be found in the dist folder:
                
        .. code-block:: bash

            python setup.py freeze
            python setup.py bdist_msi

Ubuntu/Debian Build:
====================

    * Install python 3.7.x 64bit (may already be installed)
    * Install some necessary dependencies
        
        .. code-block:: bash
    
            sudo apt-get install python-pip python-virtualenv python3.7-dev

    * Update pip to the newest version and install some other requirements:
    
        .. code-block:: bash
    
            pip install -U pip
            pip install -U virtualenvwrapper
            source /usr/local/bin/virtualenvwrapper.sh
    
    * Create the virtualenv and activate it:
    
        .. code-block:: bash
    
            mkvirtualenv idfplus
            workon idfplus
    
    * Download idfplus source:

        * Use mercurial to download the lasted development release:
        
        .. code-block:: bash
        
            hg clone https://bitbucket.org/mattdoiron/idfplus/
        
        * Move to the root directory of the downloaded idfplus source
        
    * Install dependencies:

        .. code-block:: bash

            pip install -r requirements.txt
            pip install -r requirements-dev.txt

    * Use setup.py to first freeze the application:

        .. code-block:: bash

            python setup.py freeze

    * Use scripts/build_deb.sh to package for Ubuntu (versions greater to or equal to the current version). The deb file will be found in the dist folder:

        .. code-block:: bash

            build_deb.sh deb
