Changelog
=========

v0.2.0, October xx, 2019

* Update to use PySide2 and Python 3.7.
* Lots of bug fixes.

v0.1.0, February xx, 2016

* Self-contained .msi installer for Windows 7+.
* Self-contained .deb installer for Ubuntu 14.04+.
* Simple wizard to help direct IDF+ to the right idd file.
* Search and replace with advanced querying.
* Jump menu in toolbar and right-click menu.
* Text wrapping in class table fields.
* IDF and IDD parsers are no longer case sensitive.
* Cached IDD files are now versioned to allow handling changes to the schema.
* Field units can optionally be displayed in cells and/or headers.
* References to/from cells are tracked and displayed in the References widget (not currently working for nodes)
* Cell background colours will now highlight when there is a broken/unused reference.
* Update versions of most dependencies
* Ability to choose to save state of units and hidden classes in IDFFile.
* Changes to current IDF file by external program will be detected and reload offered.
* Update dev documentation. Still no user documentation.
* Ability to "Open in folder" now works on Windows and Ubuntu.
* Ability to open current file in the default text editor.
* Many, many bug fixes and significant code cleanup/refactoring.

v0.0.3, January 18, 2015

* Fixed bug that prevented the preferences window from opening.
* Fixed Issue #25 that prevented idf files from being opened if the version object name was capitalized.
* Added a dialog to warn users of invalid idf object names.
* Fixed line endings for comments. They should now also be operating-system specific.
* Version bump for a few internal dependencies.
* Misc code cleanup.

v0.0.2, January 13, 2015

* Comments widget is now editable, allowing users to edit object-level comments within the editor.
* Log viewer has been reworked to be more memory efficient and should now work on windows.
* File save status should now be displayed properly in title bar and user will be prompted to save un-saved changes before exiting.
* Version bump for various internal dependencies.
* The editor should now use line endings specific to the operating system on which a file is saved.
* Fonts and colours should be more evenly applied throughout the editor.
* Misc code cleanup.

v0.0.1, November 15, 2014 -- Initial release.

