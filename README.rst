IDF+ Editor
===========
      
IDF+ is an enhanced editor for idf files—the text-based, simulation input files for
EnergyPlus_. In creating the tool, I've attempted to embrace the concepts and ideas
that I find most useful in my every-day building energy modelling. I've `written these
ideas in a "manifesto"`_ (rather, I discovered and developed the concepts as I created
the tool and used others). I use the official IDF Editor that comes with EnergyPlus
every day—it is the primary tool I use for interacting with IDF files. I have come
to respect it and think it is probably the best tool out there right now for working
with IDF files, however, it also has some significant limitations that I decided
to address. The working name I've chosen is IDF+, but I am hoping to find something
a bit more original as development progresses (suggestions are welcome!).

.. _EnergyPlus: http://www.energyplus.gov/
.. _written these ideas in a "manifesto": https://mindfulmodeller.ca/manifesto-good-energy-modelling-tools/

See the Downloads_ section for zip files containing the editor. There are not currently
any installers so simply extract the files and run idfplus.exe (on windows) or idfplus
on Ubuntu. You can run the editor in its uncompiled form on any machine that has
Python v2.7.x and the appropriate dependencies. See the Doc folder for more info.

.. image:: https://bitbucket.org/mattdoiron/idfplus/raw/default/resources/idfplusscreenshot.png
   :width: 300
   :target: screenshot_

.. _Downloads: https://bitbucket.org/mattdoiron/idfplus/downloads/
.. _screenshot: https://bitbucket.org/mattdoiron/idfplus/raw/default/resources/idfplusscreenshot.png
     
Open Source and Cross Platform
------------------------------

The tool is written in Python_ (v2.7.14) using PySide2_ 5.12.1 for a graphical library, and
the source code is available under the GPLv3 open source licence. It is currently
working on both Ubuntu 16.04+ and Windows 7/8/10, but will eventually work on Mac OSX
as well.

.. _Python: https://www.python.org/
.. _PySide2: https://www.qt.io/qt-for-python

Lightweight Editor
------------------

The tool continues in the spirit of the official editor in that it's a lightweight tool
that interacts as directly as possible with the contents of the IDF files.

Full Undo Support
-----------------

All primary editing features will support undo. There are bugs at the moment, but cut,
copy, paste, delete and duplicate will be 'undoable'. The undo history can be navigated
allowing a user to return to previous points in the model's recent history (within the
given editing session).

Filter and Transpose
--------------------

Both the list of classes and objects are search/filterable. This means a user can show
only objects or classes containing arbitrary bits of text. The editing actions can then
be performed on this subset of objects. The object list can also be transposed
(rows/columns reversed) to show a more traditional spreadsheet-like view.

Highly Flexible Interface
-------------------------

Each of the main interface elements, such as the class list or comments box, can be
moved around and resized as a user prefers, or even "undocked" from the main interface
altogether to be positioned on a secondary monitor.

Helpful But Not Annoying
------------------------

I've tried, and continue, to build-in useful features like autocomplete in fields that
display a large number of items in the dropdown box. Common features and help items
will also be available from the context menu.

Future Development
------------------

On the roadmap are features such as search and replace, visualization of relationships
between objects, enhanced contextual menus and help, as well as improvements to
speed and visual appearance. Behind the scenes, I intend to implement a more offical
development process based on test-driven development and automate testing and
the installer building process.

Please Note!
------------

This software is at an alpha stage! This means that it is for testing purposes only
and should not be used for real projects! I would, however, appreciate any feedback
and suggestions on how the editor can be improved. Please submit `an issue`_ if you
find any bugs.

.. _an issue: https://bitbucket.org/mattdoiron/idfplus/issues
