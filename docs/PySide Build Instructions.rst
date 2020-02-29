Instructions for Building PySide
================================

NOTE: These are no longer required if you're using pythong 3.7 and PySide2. Simply install via pip.

These are slightly modified installation instruction from: http://pyside.readthedocs.org/en/latest/building/linux.html

Install prerequisites

.. code-block:: bash

    sudo aptitude install build-essential git cmake libqt4-dev libphonon-dev python2.7-dev libxml2-dev libxslt1-dev qtmobility-dev python-pip python-sphinx

Install wheel

.. code-block:: bash

    sudo pip2.7 install -U wheel

Clone the repository to a local dir

.. code-block:: bash

    git clone https://github.com/PySide/pyside-setup.git pyside-setup

Change to the dir

.. code-block:: bash

    cd pyside-setup

Build the specific version (standalone) as a wheel or egg. Wheel seems to be broken for my Ubuntu 14.04 setup!

.. code-block:: bash

    python2.7 setup.py bdist_wheel --qmake=/usr/bin/qmake-qt4 --version=1.2.4 --standalone
    
or

.. code-block:: bash

    python2.7 setup.py bdist_egg --qmake=/usr/bin/qmake-qt4 --version=1.2.4 --standalone

Install the newly created file

.. code-block:: bash

    sudo pip2.7 install dist/PySide-1.2.4-cp27-none-linux-x86_64.whl

or

.. code-block:: bash

    sudo easy_install install dist/PySide-1.2.4-cp27-none-linux-x86_64.egg

Or install into a virtualenv

.. code-block:: bash

    bin/pip2.7 install ../dist/PySide-1.2.4-cp27-none-linux-x86_64.egg

Run the post-install script

.. code-block:: bash

    sudo python2.7 pyside_postinstall.py -install

or from a virtualenv

.. code-block:: bash

    bin/python bin/pyside_postinstall.py -install

The following also worked once:

.. code-block:: bash

    pip install --use-wheel PySide

