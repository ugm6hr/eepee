#!/usr/bin/env python
# Raja S
# Time-stamp: <Last  modified by Raja S on 03.06.2009 at 20:21:02 on tp>

"""Home brew a build script"""
import sys
import os
import shutil
import glob
import commands
# 
sourcedir = '/data/docs/programming/python/epviewer/svnlocal/trunk'
pyfiles = ['playlist_select.py',
'eepee.py',
'geticons.py',
'install.py',
'config_manager.py',
'customrubberband.py']

other_files = ['AUTHORS',
'CHANGES',
'eepee',
'eepee.desktop',
'eepee.png',
'LICENSE',
'README']

sys.path.append(sourcedir)
import eepee

class Bot():
    """The bot that builds"""
    def __init__(self, version):
        self.version = version
        self.basedir = os.path.abspath(os.curdir)

    def makebuilddir(self):
        """make a directory with version name
        """
        self.workingdir = os.path.join(self.basedir, 'eepee-' + str(self.version))
        if os.path.exists(self.workingdir):
            print 'removing old directory....\n'
            shutil.rmtree(self.workingdir)
        os.mkdir(self.workingdir)
        print 'created directory %s ....\n' %(self.workingdir)

    def copyfiles(self):
        """copy needed files"""
        needed_files = pyfiles + other_files
        for f in needed_files:
            fullname = os.path.join(sourcedir, f)
            shutil.copy(fullname, self.workingdir)
        print "copied all the files...\n"

    def runchecks(self):
        """all needed checks"""
        # are there other source files
        print "checking for files not added"
        allpyfiles = glob.glob(os.path.join(sourcedir, '*.py'))
        files_not_added = []
        
        for f in allpyfiles:
            if os.path.split(f)[1] not in pyfiles:
                files_not_added.append(f)

        if len(files_not_added) > 0:        
            print 'WARNING! - these py files not added...'
            for f in files_not_added:
                print "    %s" %(f)
            print '\n'

        # is version number right
        fileversion = eepee._version
        if fileversion == self.version:
            print 'version matches....\n'
        else:
            print 'version mismatch !....\n'
        
    def createarchive(self):
        """create a tar.gz archive"""
        cmd = "tar -czf %s %s" %('eepee-' + self.version + '.tar.gz',  self.workingdir)
        st, output = commands.getstatusoutput(cmd)
        if st == 0:
            print 'archive created successfully...\n'
        else:
            print 'archive creation failed - %s....\n' %(output)

    def buildarchive(self):
        """build the archive"""
        self.makebuilddir()
        self.copyfiles()
        self.runchecks()
        self.createarchive()

def main():
    """Build the archive for installation.
    Usage - buildbot.py version_no.
    archive is built in the directory from where the script is called    
    """
    print '\n'
    print 'starting ....\n'
    version = sys.argv[1]
    
    bot = Bot(version)
    bot.buildarchive()


if __name__ == '__main__':
    main()    
    
