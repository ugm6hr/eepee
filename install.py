
#!/usr/bin/env python

# Based on the install script for comix
# http://comix.sourceforge.net/ 

"""
This script installs or uninstalls Eepee on your system.
-------------------------------------------------------------------------------
Usage: install.py [OPTIONS] COMMAND

Commands:
    install                  Install to /usr/local

    uninstall                Uninstall from /usr/local
"""

import os
import sys
import getopt
import shutil

source_dir = os.path.dirname(os.path.realpath(__file__))
install_dir = '/usr/local'

# Files to be installed, as (source file, destination directory)
FILES = (('eepee.py', 'share/eepee/eepee.py'),
         ('geticons.py', 'share/eepee/geticons.py'),
         ('customrubberband.py', 'share/eepee/customrubberband.py'),
         ('config_manager.py', 'share/eepee/config_manager.py'),
         ('playlist_select.py', 'share/eepee/playlist_select.py'),
         ('CHANGES', 'share/eepee/CHANGES'),
         ('LICENSE', 'share/eepee/LICENSE'),
         ('eepee.desktop', 'share/applications/eepee.desktop'),
         ('eepee.png', 'share/pixmaps/eepee.png'),
         ('eepee', 'bin/eepee'))

def info():
    """Print usage info and exit."""
    print __doc__
    sys.exit(1)

def install(src, dst):
    """Copy <src> to <dst>. The <src> path is relative to the source_dir and
    the <dst> path is a directory relative to the install_dir.
    """
    try:
        dst = os.path.join(install_dir, dst)
        src = os.path.join(source_dir, src)
        assert os.path.isfile(src)
        assert not os.path.isdir(dst)
        if not os.path.isdir(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        shutil.copy(src, dst)
        print 'Installed', dst
    except Exception:
        print 'Could not install', dst

def uninstall(path):
    """Remove the file or directory at <path>, which is relative to the 
    install_dir.
    """
    try:
        path = os.path.join(install_dir, path)
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            return
        print 'Removed', path
    except Exception:
        print 'Could not remove', path

def check_dependencies():
    """Check for required and recommended dependencies."""
    required_found = True
    recommended_found = True
    print 'Checking dependencies ...\n'
    print 'Required dependencies:'

    try:
        import wx
        assert wx.__version__ >= '2.6'
        print '    wxpython ........................ OK'
    except ImportError:
        print '    wxpython .................... Not found'
        required_found = False

    try:
        import Image
        assert Image.VERSION >= '1.1.5'
        print '    Python Imaging Library ....... OK'
    except ImportError:
        print '    !!! Python Imaging Library ... Not found'
        required_found = False
    except AssertionError:
        print '    !!! Python Imaging Library ... version', Image.VERSION,
        print 'found'
        print '    !!! Python Imaging Library 1.1.5 or higher is required'
        required_found = False

    if not required_found:
        print '\nCould not find all required dependencies!'
        print 'Please install them and try again.'
        sys.exit(1)

# ---------------------------------------------------------------------------
# Install eepee.
# ---------------------------------------------------------------------------
args = sys.argv[1]

if args == 'install':
    check_dependencies()
    print 'Installing eepee to', install_dir, '...\n'
    if not os.access(install_dir, os.W_OK):
        print 'You do not have write permissions to', install_dir
        sys.exit(1)
    for src, dst in FILES:
        install(src, dst)

# ---------------------------------------------------------------------------
# Uninstall eepee
# ---------------------------------------------------------------------------
elif args == 'uninstall':
    print 'Uninstalling eepee from', install_dir, '...\n'
    if not os.access(install_dir, os.W_OK):
        print 'You do not have write permissions to', install_dir
        sys.exit(1)
    for src, dst in FILES:
        uninstall(dst)
    uninstall('~/.eepee.rc')
    
else:
    info()

