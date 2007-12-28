#!/usr/bin/python
"""
An application for viewing and analyzing ECGs and EP tracings
"""

from __future__ import division
import wx, Image, os, copy, sys
from customrubberband import RubberBand
from geticons import getBitmap
from slide import Slide

## Import Image plugins separately and then convince Image that is
## fully initialized - needed when compiling for windows, otherwise
## I am not able to open tiff files with the windows binaries
import PngImagePlugin
import BmpImagePlugin
import TiffImagePlugin
import GifImagePlugin
import JpegImagePlugin
Image._initialized = 2
###

TITLE          = "EP viewer"
ABOUT          = """ 
An application to view and analyze EP tracings\n   
Author: Raja S. \n 
rajajs@gmail.com\n 
For more information and for updates visit\n  
http:\\code.google.com\p\eepee\n"""

#------------------------------------------------------------------------
#wx IDs

ID_ABOUT    =   wx.NewId()
ID_OPEN   =   wx.NewId()
ID_CALIB    =   wx.NewId()
ID_CALIPER  =   wx.NewId()
ID_EXIT     =   wx.NewId()
ID_TEXT     =   wx.NewId()
ID_STAMP    =   wx.NewId()
ID_REMOVE   =   wx.NewId()
ID_PREV     =   wx.NewId()
ID_NEXT     =   wx.NewId()
ID_JUMP     =   wx.NewId()
ID_SAVE     =   wx.NewId()
ID_FRAME    =   wx.NewId()

#--------------------------------------------------------------------------


#--------------------------------------------------------------------------
class PlayList():

    def __init__(self,filename):
        self.playlist = []
        self.nowshowing = 0   #current position in list
        if filename[-4:] == '.plst':
            self.playlistfile = filename
            self.OpenPlaylist()            
        else:
            self.MakeDefaultPlayList(filename)
            
    def MakeCustomPlayList():
        """
              Allow user to make a playlist and save it
        """
        #FIXME: To implement fully
        dlg = wx.FileDialog(self,"Select Images",style = wx.OPEN | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
           self.playlist = dlg.GetPaths() #FIXME: not unicode !
        # The user did not select anything
        else:
            print 'Nothing was selected.'
        # Destroy the dialog
        dlg.Destroy()
    
    def MakeDefaultPlayList(self, filename):
        """
        Make a playlist by listing all image files
        in the directory beginning from the selected
        file
        """
        dirname,currentimage = os.path.split(filename)
        allfiles = os.listdir(dirname)
                
        for eachfile in allfiles:
            if eachfile.split('.')[-1].lower() in \
               ['bmp','png','jpg','jpeg','tif','tiff','gif']:
                   self.playlist.append(os.path.join(dirname,eachfile))
        self.playlist.sort()
        self.nowshowing = self.playlist.index(filename)
        
    def SavePlayList(self,event):
        """
           Save a playlist that as been created
        """
        playlistfile = wx.FileDialog(self,"Save file as",style = wx.SAVE)
        #FIXME: check for cancel, etc.
        playlistfile += '.lst'
        fi = open(playlistfile,'w')
        for filename in self.playlist:
            fi.write(filename+ '\n')
        fi.close()
        
    def OpenPlayList(self,event):
        """
              open an existing playlist
        """
        self.playlist = playlistfile.read().split('\n')
        #FIXME: May have to remove spaces
#-------------------------------------------------------------------------------


#--------------------------------------------------------------------------------    
class NotePad(wx.Panel):

    def __init__(self, parent,readonly):
        wx.Panel.__init__(self, parent)
        
        #readonly flag is set for the slide
        if readonly:
            self.pad = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE | wx.TE_READONLY)
        else:
            self.pad = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE)
            
        s = wx.BoxSizer()
        s.Add(self.pad,1,wx.EXPAND)
        self.SetSizer(s)
        
        self.pad.Clear()
        self.parentframe = wx.GetTopLevelParent(self) #top level parent to set text
        
    def FillNote(self,imagefilename):
        """
        Fill the notebook at beginning
        with previously stored notes if they 
        have been stored
        """
        (w,h) = self.GetSize()#because GetSize doesnt work in init
        self.pad.SetSize(( w*0.6 ,h*0.9 )) 
        self.pad.SetPosition(( w*0.2 ,h*0.05 )) #Now I have a nicely centered potrait page
        self.notefile = '.'.join((imagefilename.rsplit('.',1)[0],'note')) #Splits once at rightmost '.'
        if os.path.exists(self.notefile):
            self.parseNote()
            self.pad.write(self.notes)
           
        else:   #else start empty
            self.notes = ''
            self.parentframe.frameextent = (0,0,0,0)
            self.parentframe.panel.caliper.calib = 0
            self.pad.Clear()
            
    def SaveNote(self):
        """
        Save the note to the file with 
              same name as image with suffix 'note'
        """
        
        self.notes = self.pad.GetValue()
        
        ## dont litter with a note if there is nothing to note !
        if self.notes == '' and \
           self.parentframe.panel.caliper.calib == 0 and \
           self.parentframe.frameextent == (0,0,0,0):
            return
        
        fi = open(self.notefile,'w')
        fi.write('Calibration:%s\n' % (self.parentframe.panel.caliper.calib)) 
        fi.write('Zoomframe:%s,%s,%s,%s\n' % (self.parentframe.frameextent[0],
                                              self.parentframe.frameextent[1],
                                              self.parentframe.frameextent[2],
                                              self.parentframe.frameextent[3]))
        fi.write(self.notes)
        fi.close()
        
    def parseNote(self): 
        """
        Parse the stored note and extract the information
        Notes can be a multi-line entry and will be stored at 
        the end of the file.
        Single line entries come before. 
        All have a header of the 'somestring:' followed by the data itself.
        Empty lines are not allowed except at the end.        
        """
        
        lines_to_parse = open(self.notefile,'r').readlines()
        linecount = 0
        
        try:
            self.parentframe.panel.caliper.calib = float(lines_to_parse[0].lstrip('Calibration:'))
            self.parentframe.frameextent = tuple([int(x) for x in lines_to_parse[1].lstrip('Zoomframe:').split(',')])
            self.notes = ''.join(lines_to_parse[2:])
            
        #If cannot parse, dump the whole thing on the pad
        except:
            self.notes = ''.join(lines_to_parse[:])
            self.parentframe.frameextent = (0,0,0,0) #FIXME: should be in initalize
            self.parentframe.panel.caliper.calib = 0 #FIXME: should be in initalize
        
        if self.parentframe.panel.caliper.calib == 0:
            self.parentframe.panel.caliper.units = 'pixels'  #FIXME: base this on value itself
        else:
            self.parentframe.panel.caliper.units = 'ms'
        
#--------------------------------------------------------------------------------        


#-------------------------------------------------------------------------------
class Caliper():

    def __init__(self,parent):

        #initialize flags
        self.CALIBRATE = "False"
        self.STATUS = "None"
        self.CALIPERMOVE = "None"

        #initialize positions
        self.left_x = 0
        self.right_x = 0
        self.horiz_y = 0
        self.prev_x = 0
        self.prev_y = 0
        self.calib = 0
        
        #initialize pen
        self.pen =wx.Pen(wx.Colour(255, 255, 255), 1, wx.SOLID)
        self.units = "pixels"
    
    def DrawCaliper(self,dc,coords):
        dc.SetLogicalFunction(wx.XOR)
        dc.BeginDrawing()
        dc.SetPen(self.pen)
        dc.DrawLine(*coords)
        dc.EndDrawing()
        
    def ClickLeft(self,dc): #first line of caliper or calibrate measure
        #erase caliper so that next XOR (for right caliper will draw it)
        coords = (self.prev_x, 0, self.prev_x, self.height)
        self.DrawCaliper(dc,coords)
        self.left_x = self.prev_x
        self.STATUS = "Second"
        
    def ClickRight(self): #second line for caliper only
        self.STATUS = "Done"
        self.right_x = self.prev_x
        self.horiz_y = self.prev_y
        self.prev_x = 0
        self.prev_y = 0
        
        #swap if not in sequence
        if self.left_x > self.right_x:
            self.left_x,self.right_x = self.right_x,self.left_x
            
    def ClickCalibrate(self,dc): #second line for calibrate measure
        self.STATUS = "None"
        self.CALIBRATE = "False"
        
        self.Calibrate()
        #remove calipers
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
        self.DrawCaliper(dc,(self.left_x, 0, self.left_x, self.height))
        self.DrawCaliper(dc,(self.left_x,self.prev_y,self.prev_x,self.prev_y))
 
        self.prev_x = 0
        self.prev_y = 0
        
    def Calibrate(self):
        dialog = wx.TextEntryDialog(None, "Enter distance in ms:","Calibrate")
        if dialog.ShowModal() == wx.ID_OK:
            cal = dialog.GetValue()
            self.calib = int(cal)/self.distance  #multiply pixels by scale to get ms
            self.units = "ms"
            
            
        dialog.Destroy() 
        
    def ClickMove(self,pos):
        if self.CALIPERMOVE == "Whole":
            self.STATUS = "MoveWhole"
            self.left_xoffset = self.left_x - pos.x
            self.right_xoffset = self.right_x - pos.x
            self.prev_x = self.left_x
            self.prev_y = self.horiz_y
        
        if self.CALIPERMOVE == "First":
            self.STATUS = "MoveFirst"
            self.prev_x = self.left_x
            self.prev_y = self.horiz_y
            
        if self.CALIPERMOVE == "Second":
            self.STATUS = "MoveSecond"
            self.prev_x = self.right_x
            self.prev_y = self.horiz_y    
            
    def ClickStopWhole(self):
        self.left_x = self.prev_x
        self.right_x = self.prev_x + self.right_xoffset - self.left_xoffset
        self.horiz_y = self.prev_y
        
    def ClickStopFirst(self):
        self.left_x = self.prev_x
        self.horiz_y = self.prev_y
        
    def ClickStopSecond(self):
        self.right_x = self.prev_x
        self.horiz_y = self.prev_y
        
    def MoveFirst(self,dc,pos):
        
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
                   
        #draw new line in new position
        self.DrawCaliper(dc,(pos.x, 0, pos.x, self.height))
        self.prev_x = pos.x
        
    def MoveSecond(self,dc,pos):
        #erase second caliper
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
        #erase horizontal line
        self.DrawCaliper(dc,(self.left_x,self.prev_y,self.prev_x,self.prev_y))
                    
        #draw second caliper
        self.DrawCaliper(dc,(pos.x, 0, pos.x, self.height))
        #draw horizontal line
        self.DrawCaliper(dc,(self.left_x,pos.y,pos.x,pos.y))
        
        self.right_x = self.prev_x = pos.x
        self.prev_y = pos.y
        
        self.MeasureDistance(pos)
                
    def ChangeIcon(self,pos):
        #change cursor according to position
        onHorizbar        = (abs(pos.y-self.horiz_y) < 5)
        betweenCalipers   = (pos.x >= self.left_x and pos.x <= self.right_x)
        onCaliper1        = (abs(pos.x-self.left_x)<5)
        onCaliper2        = (abs(pos.x-self.right_x)<5)
                        
        if betweenCalipers and onHorizbar:
            self.CALIPERMOVE = "Whole"
        elif onCaliper1 and not onHorizbar:
            self.CALIPERMOVE = "First"
        elif onCaliper2 and not onHorizbar:
            self.CALIPERMOVE = "Second"
        else:
            self.CALIPERMOVE = "None"
            
    def RePosWhole(self,dc,pos):
        
        #erase prev cursor
        prev_x2 = self.prev_x - self.left_xoffset+self.right_xoffset
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
        self.DrawCaliper(dc,(prev_x2, 0, prev_x2, self.height))
        self.DrawCaliper(dc,(self.prev_x,self.prev_y,prev_x2,self.prev_y))
                   
        #draw new cursor in new position
        self.DrawCaliper(dc,(pos.x+self.left_xoffset, 0, pos.x+self.left_xoffset, self.height))
        self.DrawCaliper(dc,(pos.x+self.right_xoffset, 0, pos.x+self.right_xoffset, self.height))
        self.DrawCaliper(dc,(pos.x+self.left_xoffset, pos.y, pos.x+self.right_xoffset, pos.y))
                
        self.prev_x = pos.x + self.left_xoffset
        self.prev_y = pos.y            
        
    def RePosFirst(self,dc,pos):
        
        #erase first caliper
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
        #erase horizontal line
        self.DrawCaliper(dc,(self.right_x,self.prev_y,self.prev_x,self.prev_y))
                    
        #draw new
        #draw second caliper
        self.DrawCaliper(dc,(pos.x, 0, pos.x, self.height))
        #draw horizontal line
        self.DrawCaliper(dc,(self.right_x,pos.y,pos.x,pos.y))
        
        self.left_x = self.prev_x = pos.x #so that distance is right
        self.prev_y = pos.y
        
        self.MeasureDistance(pos)
                       
    def RePosSecond(self,dc,pos):
        #erase second caliper
        self.DrawCaliper(dc,(self.prev_x, 0, self.prev_x, self.height))
        #erase horizontal line
        self.DrawCaliper(dc,(self.left_x,self.prev_y,self.prev_x,self.prev_y))
        
        self.right_x = self.prev_x = pos.x
        self.prev_y = pos.y
                
        #draw new
        #draw second caliper
        self.DrawCaliper(dc,(pos.x, 0, pos.x, self.height))
        #draw horizontal line
        self.DrawCaliper(dc,(self.left_x,pos.y,pos.x,pos.y))
        
        self.MeasureDistance(pos)
                        
    def Remove(self,dc):
        #erase the calipers
        self.DrawCaliper(dc,(self.left_x, 0, self.left_x, self.height))
        self.DrawCaliper(dc,(self.left_x,self.horiz_y,self.right_x,self.horiz_y))
        self.DrawCaliper(dc,(self.right_x, 0, self.right_x, self.height))
        #reset variables
        self.STATUS = "None"
        self.CALIPERMOVE = "None"
        self.left_x = 0
        self.right_x = 0
        self.horiz_y = 0
        self.prev_x = 0
        self.prev_y = 0
        self.measurement = ""
        
    def Stamp(self,dc):
        #first XOR over the calipers
        #dc.SetLogicalFunction(wx.SET)
        self.DrawCaliper(dc,(self.left_x, 0, self.left_x, self.height))
        self.DrawCaliper(dc,(self.right_x, 0, self.right_x, self.height))
        self.DrawCaliper(dc,(self.left_x,self.horiz_y, self.right_x, self.horiz_y))

        #now do a copy blit with a black pen
        dc.SetLogicalFunction(wx.COPY)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1, wx.SOLID))
        dc.DrawLine(self.left_x, 0, self.left_x, self.height)
        dc.DrawLine(self.right_x, 0, self.right_x, self.height)
        dc.DrawLine(self.left_x,self.horiz_y, self.right_x, self.horiz_y)
 
        #Write measurement
        dc.DrawText(self.measurement,(self.left_x+self.right_x)/2,self.horiz_y-15)
        #reset positions
        self.STATUS = "None"
        self.CALIPERMOVE = "None"
        self.left_x = 0
        self.right_x = 0
        self.horiz_y = 0
        self.prev_x = 0
        self.prev_y = 0
        self.measurement = ""
                
    def MeasureDistance(self,pos):

        self.distance = abs(self.left_x-self.right_x)  
        if self.units == "ms":
            self.displaydistance = self.distance*self.calib
        else:
            self.displaydistance = self.distance
        self.measurement = ' '.join((str(int(self.displaydistance)),self.units))
#----------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------                        
#The custom window
class CustomWindow(wx.Window):
    
    def __init__(self, parent, ID):
        
        wx.Window.__init__(self, parent, ID)
        self.frame = wx.GetTopLevelParent(self) #top level parent to set statustext
        self.prevpos = wx.Point(0,0) 
        
        #Bind mouse events
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnClick)
        self.Bind(wx.EVT_LEFT_UP,self.OnRelease)
               
        wx.EVT_PAINT(self, self.OnPaint)
        
        self.units = "pixels" #default when we start
        self.caliper = Caliper(self)
        
        self.rubberband = RubberBand(self)

    def OnRelease(self,event):
        if self.rubberband.enabled:
            self.rubberband.handleMouseEvents(event)   
        else:
            pass
        
    def OnClick(self,event):
        
        #rubberband if enabled
        if self.rubberband.enabled:
            self.rubberband.handleMouseEvents(event)   
        
        #Calipers are on and this is the first caliper
        elif self.caliper.STATUS == "First":
            dc = wx.ClientDC(self)
            self.caliper.ClickLeft(dc)
            
            self.frame.toolbar.EnableTool(ID_OPEN , False)
            self.frame.toolbar.EnableTool(ID_CALIPER , False)
            self.frame.toolbar.EnableTool(ID_CALIB   , False)
            #self.frame.toolbar.EnableTool(ID_REMOVE  , False)
            #self.frame.toolbar.EnableTool(ID_STAMP   , False)
            self.frame.toolbar.EnableTool(ID_PREV    , False)
            self.frame.toolbar.EnableTool(ID_NEXT    , False)
            self.frame.toolbar.EnableTool(ID_SAVE    , False)
            
            self.frame.AcceptKeyPress = False
                  
        #Calipers and not calibrate, second caliper
        elif self.caliper.STATUS == "Second" and self.caliper.CALIBRATE == "False":
            self.caliper.ClickRight()
            
            self.frame.toolbar.EnableTool(ID_OPEN , True)
            self.frame.toolbar.EnableTool(ID_REMOVE, True)
            self.frame.toolbar.EnableTool(ID_STAMP, True)
            self.frame.toolbar.EnableTool(ID_PREV    , True)
            self.frame.toolbar.EnableTool(ID_NEXT    , True)
            self.frame.toolbar.EnableTool(ID_SAVE    , True)
            
            self.frame.AcceptKeyPress = True
        
        #calibrate, second
        elif self.caliper.STATUS == "Second" and  self.caliper.CALIBRATE == "True":
            dc = wx.ClientDC(self)
            self.caliper.ClickCalibrate(dc)
            self.caliper.STATUS = "None"
            self.caliper.CALIBRATE = "False"
            self.frame.SetStatusText('Calibrated',2)
            
            self.frame.AcceptKeyPress = True
            
            #self.frame.toolbar.EnableTool(ID_REMOVE, True)
            #self.frame.toolbar.EnableTool(ID_STAMP, True)
            self.frame.toolbar.EnableTool(ID_OPEN , True)
            self.frame.toolbar.EnableTool(ID_PREV    , True)
            self.frame.toolbar.EnableTool(ID_NEXT    , True)
            self.frame.toolbar.EnableTool(ID_SAVE    , True)
            self.frame.toolbar.EnableTool(ID_CALIB   , True)
            self.frame.toolbar.EnableTool(ID_CALIPER , True)
            
        #ready to move
        elif self.caliper.STATUS == "Done":  #caliper is drawn
            pos = event.GetPosition()
            self.caliper.ClickMove(pos)
        
        #if we are moving, stop it
        elif self.caliper.STATUS == "MoveWhole":
            self.caliper.STATUS = "Done"
            self.caliper.ClickStopWhole()
                               
        elif self.caliper.STATUS == "MoveFirst":
            self.caliper.STATUS = "Done"
            self.caliper.ClickStopFirst()
            
        elif self.caliper.STATUS == "MoveSecond":
            self.caliper.STATUS = "Done"      
            self.caliper.ClickStopSecond()
        
    def OnMotion(self, event):
        
        #rubberband if enabled
        if self.rubberband.enabled:
            self.rubberband.handleMouseEvents(event)   
            
        #first caliper        
        elif self.caliper.STATUS == "First":
            #erase prev line
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.MoveFirst(dc,pos)
        
        #second caliper
        elif self.caliper.STATUS == "Second":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.MoveSecond(dc,pos)
            self.frame.SetStatusText(self.caliper.measurement,3)
                    
        elif self.caliper.STATUS == "Done":
            #get position
            pos = event.GetPosition()
            self.caliper.ChangeIcon(pos)
        
            if self.caliper.CALIPERMOVE == "Whole":
                self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        
            elif self.caliper.CALIPERMOVE == "First":
                self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
        
            elif self.caliper.CALIPERMOVE == "Second":
                self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))           
        
            elif self.caliper.CALIPERMOVE == "None":
                self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))    
                        
        elif self.caliper.STATUS == "MoveWhole": #move both cursors and horiz
            #we are near horiz bar
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosWhole(dc,pos)
                    
        elif self.caliper.STATUS == "MoveFirst":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosFirst(dc,pos)
        
            self.frame.SetStatusText(self.caliper.measurement,3)
                
        elif self.caliper.STATUS == "MoveSecond":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosSecond(dc,pos)
            
            self.frame.SetStatusText(self.caliper.measurement,3)
            
    def CaliperRemove(self,event):
        dc = wx.ClientDC(self)
        self.caliper.Remove(dc)
        self.frame.toolbar.EnableTool(ID_CALIPER , True)
        self.frame.toolbar.EnableTool(ID_CALIB   , True)
        
    def CaliperStamp(self,event):
        dc = wx.ClientDC(self)
        self.caliper.Stamp(dc)
        self.frame.toolbar.EnableTool(ID_CALIPER , True)
        self.frame.toolbar.EnableTool(ID_CALIB   , True)
       
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.bmp <> None:
            memdc = wx.MemoryDC()
            memdc.SelectObject(self.bmp)
            dc.Blit(0,0,self.GetSize()[0]-self.frame.sidepanelsize,self.GetSize()[1],memdc,0,0)
            self.prevpos =wx.Point(0,0)
#-----------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------------               
class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):

        wx.Frame.__init__(self, parent, -1, title,pos=(0,0),style = wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        ##-------------STATUSBAR----------------------------------------------------##
        #statusbar with 4 fields, first for toolbar status messages,
        #second for filename
        #third for calibration status
        #fourth for the measurements
        
        self.CreateStatusBar(4)
        
        ##--------------TOOLBAR------------------------------------------------------##
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((20,20))

        self.toolbar.AddLabelTool(ID_OPEN  , 'Open'
                                             , getBitmap("open")
                                             , longHelp='Open a file')
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(ID_CALIB   , 'Calibrate'
                                             , getBitmap("calibrate")
                                             , longHelp='Calibrate with known measurement')
        self.toolbar.AddLabelTool(ID_CALIPER , 'Caliper'
                                             ,  getBitmap("calipers")
                                             , longHelp='Start a new caliper')
        self.toolbar.AddLabelTool(ID_REMOVE  , 'Remove Caliper'
                                             ,  getBitmap("removecalipers")
                                             , longHelp='Remove the current caliper' )
        self.toolbar.AddLabelTool(ID_STAMP   , 'Stamp Caliper'
                                             ,  getBitmap("stampcalipers")
                                             , longHelp='Print the caliper on image')
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(ID_PREV    , 'Previous'
                                             ,  getBitmap("previous")
                                             , longHelp='Open previous image in playlist')
        self.toolbar.AddLabelTool(ID_NEXT    , 'Next'           
                                             ,  getBitmap("next")
                                             , longHelp='Open next image in playlist')
        
        self.toolbar.AddSeparator()
        
        ### Disable for now
        #self.toolbar.AddCheckLabelTool(ID_FRAME   , 'Select frame'          
        #                                     ,  getBitmap("frame")
        #                                     , longHelp='Select frame for zoom')
        ####
        
        self.toolbar.AddLabelTool(ID_SAVE    , 'Save'
                                             ,  getBitmap("save")
                                             , longHelp='Save the image with stamped calipers')
        self.toolbar.AddLabelTool(ID_EXIT    , 'Exit'           
                                             ,  getBitmap("exit")
                                             , longHelp='Exit the application')
        self.toolbar.AddSeparator()        
        self.toolbar.AddLabelTool(ID_ABOUT   , 'About'          
                                             ,  getBitmap("about")
                                             , longHelp='About Eepee')
        
        
        self.toolbar.Realize()
        
       
        ##----------------------------------------------------------------------------##

        ##-----------SPLITTER----------------------------------------------------------##                
        self.splitter = wx.SplitterWindow(self, style=wx.NO_3D|wx.SP_3D)
        self.splitter.SetMinimumPaneSize(1)
        self.notebookpanel = wx.Panel(self.splitter,-1)
        self.list = wx.ListBox(self.splitter,-1)
        self.list.Show(True)
        self.splitter.SplitVertically(self.notebookpanel,self.list)
        self.splitter.Unsplit() #I dont know the size yet
        ##----------------------------------------------------------------------------##

        ##-----------NOTEBOOK--------------------------------------------------------##
        self.nb = wx.Notebook(self.notebookpanel)
        
        self.notepad = NotePad(self.nb,False)
        self.panel = CustomWindow(self.nb,-1)
        
        #~ self.slide1 = Slide(self.nb)
        #~ self.slide1.drawSlide()
        #~ 
        #~ self.slide2 = Slide(self.nb)
        #~ self.slide2.drawSlide()
                        
        self.nb.AddPage(self.panel, "Tracing")
        self.nb.AddPage(self.notepad, "Notes")
        #~ self.nb.AddPage(self.slide1, "Slide 1")
        #~ self.nb.AddPage(self.slide2, "Slide 2")
        
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.notebookpanel.SetSizer(sizer)
        
        ##----------------------------------------------------------------------------##        
        
        wx.EVT_MENU(self,  ID_ABOUT,   self.About)
        wx.EVT_MENU(self,  ID_OPEN,  self.ChooseImage)
        wx.EVT_MENU(self,  ID_EXIT,    self.OnClose)
        wx.EVT_MENU(self,  ID_CALIPER, self.CaliperStart)
        wx.EVT_MENU(self,  ID_CALIB,   self.CalibrateMeasure)
        wx.EVT_MENU(self,  ID_TEXT,    self.TextEntry)       
        wx.EVT_MENU(self,  ID_REMOVE,  self.panel.CaliperRemove)
        wx.EVT_MENU(self,  ID_STAMP,   self.panel.CaliperStamp)       
        wx.EVT_MENU(self,  ID_PREV,    self.PrevOnList)
        wx.EVT_MENU(self,  ID_NEXT,    self.NextOnList)
        wx.EVT_MENU(self,  ID_SAVE,    self.SaveImage)
        wx.EVT_MENU(self,  ID_FRAME,   self.SelectFrame)
        wx.EVT_CLOSE(self, self.OnClose)
                
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.JumpInList)
        
        #bind keyboard events in the panel
        self.panel.Bind(wx.EVT_KEY_DOWN,self.onKeyPress)
        
        #catch page changes in the notebook
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self.nb, -1, self.onPageChange)
        
        self.RESIZE_FLAG = "TRUE"
        self.rootdir = os.getcwd()
        self.playlist = []
        self.BITMAP_FLAG = "notexists"
        self.panel.bmp = None
        self.sidepanelsize = 60 #side of the panel showing playlist
        self.IMAGE_SELECTED = "False"  #Has an image been selected yet?
        self.width = 0 #not initialized
        self.ZOOMFRAMEON = False
        # ready to accept keypress ?
        self.AcceptKeyPress = True
        
        self.slides = []
        self.slide_delimiter = '=='
        self.title_delimiter = '**'
        
        self.InitializeAll()
    
    def onKeyPress(self,event):
        """
        Bind events to keyboard shortcuts
        """
        if not self.AcceptKeyPress:
            return
         
        kcode = event.GetKeyCode()
         
        if kcode == 79: # 'o'
            self.ChooseImage(event)
        elif kcode == 66: # 'b'
            self.CalibrateMeasure(event)
        elif kcode == 67: # 'c'
            self.CaliperStart(event)
        elif kcode == 84: # 't'
            self.panel.CaliperStamp(event)
        elif kcode == 82: # 'r'
            self.panel.CaliperRemove(event)
        elif kcode == 314: # left arrow
            self.PrevOnList(event)
        elif kcode == 316: # right arrow
            self.NextOnList(event)
        elif kcode == 83: # 's'
            self.SaveImage(event)
        elif kcode == 81: # 'q'
            self.OnClose(event)
    
    
    def onPageChange(self,event):
        """
        Watch out for page changes while a caliper
        is active
        """
        if self.panel.caliper.STATUS <> "None":
            self.panel.caliper.STATUS = "None"
            self.toolbar.EnableTool(ID_CALIPER , True)
            self.toolbar.EnableTool(ID_CALIB   , True)
            self.toolbar.EnableTool(ID_REMOVE  , False)
            self.toolbar.EnableTool(ID_STAMP   , False)
    
    def SelectFrame(self,event):
        """
        Select the zoomframe using rubberband if not prev selected.
        If zoomframe is already on, unzoom now
        """
        #starting the rubberband
        if not self.ZOOMFRAMEON:
            
            if not self.panel.rubberband.enabled:
                #toggle frame button to off #FIXME: not working
                #self.toolbar.ToggleTool(ID_FRAME,1)
                self.panel.rubberband.enabled = True
                                
                #disable other controls
                self.toolbar.EnableTool(ID_CALIPER , False)
                self.toolbar.EnableTool(ID_CALIB   , False)
                self.toolbar.EnableTool(ID_REMOVE  , False)
                self.toolbar.EnableTool(ID_STAMP   , False)
                self.toolbar.EnableTool(ID_PREV    , False)
                self.toolbar.EnableTool(ID_NEXT    , False)
                self.toolbar.EnableTool(ID_SAVE    , False)
        
            else:
                if self.panel.rubberband.getCurrentExtent() <> None:
                    frameborders = self.panel.rubberband.getCurrentExtent()
                
                self.frameextent = list(frameborders)
                self.frameextent = [int(x/self.ratio) for x in self.frameextent]
                self.frameextent = tuple(self.frameextent)
                
                self.panel.rubberband.reset()
                self.panel.rubberband.enabled = False
                
                
                ##toggle the frame icon to 'on' position
                self.toolbar.ToggleTool(ID_FRAME,2)
                
                self.toolbar.EnableTool(ID_CALIPER , True)
                self.toolbar.EnableTool(ID_CALIB   , True)
                #self.toolbar.EnableTool(ID_REMOVE  , False)
                #self.toolbar.EnableTool(ID_STAMP   , False)
                self.toolbar.EnableTool(ID_PREV    , True)
                self.toolbar.EnableTool(ID_NEXT    , True)
                self.toolbar.EnableTool(ID_SAVE    , True)
                #self.toolbar.EnableTool(ID_FRAMEON, True)
                
                #redraw image
                self.DisplayImage()
            
        #if already zoomed in    
        else:
            self.ZOOMFRAMEON = False
            self.frameextent = (0,0,0,0)
            self.DisplayImage()
                    
    def InitializeAll(self):
        """
        Values that have to be initialized
        for every new image
        """
        
        self.panel.CALIPERFLAG = "False"
        self.panel.caliper.CALIBRATE = "False"
        self.panel.caliper.STATUS = "None"
        self.panel.caliper.CALIPERMOVE = "None"
        self.panel.caliper.measurement = ''
        
        self.SetStatusText("No file selected",1)
        self.SetStatusText("",2)
        self.SetStatusText("",3)
        
        #clear old slides
        # bug in wxpython results in some pages not getting
        # deleted at each pass
        # So I am looping till I am done
        while self.nb.GetPageCount() > 2:
            for slideindex in range(2,self.nb.GetPageCount()):
                self.nb.DeletePage(slideindex)
        self.slides = []
        
                       
        #disable these icons initially
        self.toolbar.EnableTool(ID_CALIPER , False)
        self.toolbar.EnableTool(ID_CALIB   , False)
        self.toolbar.EnableTool(ID_REMOVE  , False)
        self.toolbar.EnableTool(ID_STAMP   , False)
        self.toolbar.EnableTool(ID_PREV    , False)
        self.toolbar.EnableTool(ID_NEXT    , False)
        self.toolbar.EnableTool(ID_SAVE    , False)
        #self.toolbar.EnableTool(ID_FRAME   , False)
        #self.toolbar.EnableTool(ID_FRAMEON , False)
        #self.toolbar.ToggleTool(ID_FRAME,0)        
        
    def Alert(self,title,msg="Undefined"):
        dlg = wx.MessageDialog(self, msg,title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def About(self, event):
        self.Alert("About",ABOUT)
  
    def PrevOnList(self,event):
        self.playlist.nowshowing -= 1
        if self.playlist.nowshowing < 0: 
            self.playlist.nowshowing = len(self.playlist.playlist)-1
       
        self.InitializeAll()
        self.list.SetSelection(self.playlist.nowshowing)

        self.img = self.playlist.playlist[self.playlist.nowshowing]
        self.DisplayImage()
        
    def NextOnList(self,event):
        self.playlist.nowshowing += 1
        if self.playlist.nowshowing > len(self.playlist.playlist)-1:
            self.playlist.nowshowing = 0  
        
        self.InitializeAll()

        self.list.SetSelection(self.playlist.nowshowing)
        self.img = self.playlist.playlist[self.playlist.nowshowing]
        self.DisplayImage()
  
    def JumpInList(self,event): #double clicked on playlist to 'jump'
      self.playlist.nowshowing = self.list.GetSelection()
      self.img = self.playlist.playlist[self.playlist.nowshowing]
      self.InitializeAll()
      self.DisplayImage()
          
    def OnClose(self,event):
        #first save notes - but dont get caught with errors
        try:
            self.notepad.SaveNote()
        except:
            pass
        self.Destroy()
        
    def TextEntry(self,event):
        self.savedtext = wx.GetTextFromUser("Value","Input Value","this is the place to add notes")
        
    def CaliperStart(self,event):
        if self.panel.caliper.STATUS == "None":
            self.panel.caliper.STATUS = "First"
          
    def CalibrateMeasure(self,event):
        self.panel.caliper.STATUS = "First"
        self.panel.caliper.CALIBRATE = "True"
       
    def ScaleImage(self,im,width_win,height_win): #scale image to smaller than w x h, but maintain aspect ratio
        
        width_im, height_im = im.size
        
        if width_im/height_im > width_win/height_win:
            self.ratio = width_win / width_im
        else:
            self.ratio = height_win / height_im
       
        im = im.resize((int(width_im*self.ratio),int(height_im*self.ratio)),Image.ANTIALIAS)
        self.imagewidth,self.imageheight = im.size  # the size as displayed
        return im
    
    def makeSlide(self,slidestring,slidenum):
        """
        Make a slide and add to notebook
        Title and text for slide are obtained 
        by parsing the slide string
        slidenum is the number of the current slide
        with the slide numbers beginning with 1
        """
        
        # add a new slide - all slides are in a list
        self.slides.append(Slide(self.nb))
                
        # Name of slide is in format 'Slide (n)' 
        # n is slidenum+1 so that it starts with 1
        self.nb.AddPage(self.slides[slidenum],"Slide "+str(slidenum+1))
        
        title,text = self.parseSlideString(slidestring)
        self.slides[-1].title = title
        self.slides[-1].text = text
        
        self.slides[-1].drawSlide()
    
    def DisplayImage(self):
        
        self.SetStatusText("Loading file...",1)
        
        #If there was an image before, save the note 
        if self.IMAGE_SELECTED == "TRUE":
            self.notepad.SaveNote()
            self.notepad.pad.Clear()
        else:
            self.IMAGE_SELECTED = "TRUE"
                
        self.notepad.FillNote(self.img)  #get notes
        
        self.slidestrings = self.parseNoteString(self.notepad.notes)
        
        for slidenum in range(len(self.slidestrings)):
            self.makeSlide(self.slidestrings[slidenum],slidenum)
        
                               
        self.panel.bmp = self.GetBmpfromPIL(self.img)
        if self.panel.bmp == None:
           return 0
                
        self.rootdir = os.path.dirname(self.img)

        dc = wx.ClientDC(self.panel)
        dc.Clear()  #clear old image if still there
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.panel.bmp)

        dc.Blit(0,0,self.width-self.sidepanelsize, self.panel.caliper.height,memdc,0,0)
        
                
        self.SetStatusText(os.path.basename(self.img),1)
        
        calibrated = ( self.panel.caliper.calib <> 0 ) # Will be 0 if not calibrated
        if calibrated:
            calibstatus = 'Calibrated'
        else:
            calibstatus = 'Not calibrated'
        self.SetStatusText(calibstatus,2)
        
        #enable icons
        self.toolbar.EnableTool(ID_CALIPER, True)
        self.toolbar.EnableTool(ID_CALIB, True)
        self.toolbar.EnableTool(ID_PREV, True)
        self.toolbar.EnableTool(ID_NEXT, True)
        self.toolbar.EnableTool(ID_SAVE, True)
        self.toolbar.EnableTool(ID_FRAME, True)
        #self.toolbar.EnableTool(ID_FRAMEON, True)
        
    def parseSlideString(self,slidestring):
        """
        Parses the slide string to identify 
        the title and text for the slide
        """
        parts = slidestring.split(self.title_delimiter)
        
        #if there is no title
        if len(parts) == 1:
            title = ''
            text = slidestring
            return title, text
        
        #if there is only one title delimiter
        if len(parts) == 2:
            self.SetStatusText("Missing title delimiter in slide",3)
            return '', ''
        
        title = parts[1]
        text = slidestring.replace(self.title_delimiter+title+self.title_delimiter,'')  #elegantly allows title to be anywhere
        
        return title, text
    
 
    def parseNoteString(self,notestring):
        """
        Parse the note to identify the string(s) 
        for the slide(s)
        Will work for arbitrary number of slide strings
        """
        slidestrings = []
        
        parts = notestring.split(self.slide_delimiter)
        for i in range(1,len(parts),2):
            slidestrings.append(parts[i])
            
        if len(parts)%2 == 0:
            pself.SetStatusText("Missing slide delimiter",3)
        
        return slidestrings
        
    def DisplayPlayList(self):
        self.splitter.SplitVertically(self.notebookpanel,self.list)
        self.splitter.SetSashPosition(self.width-self.sidepanelsize, True)
        self.list.Clear()
        
        for filename in self.playlist.playlist:
            self.list.Append(os.path.split(filename)[1])
            
        self.list.SetSelection(self.playlist.nowshowing)
    
    def ChooseImage(self,event):

        filters = 'Supported formats|*.png;*.PNG;*.tif;*.TIF;*.tiff;*.TIFF;*.jpg;*.JPG;*.jpeg;*.JPEG;                                     *.bmp;*.BMP;*.gif;*.GIF'
        dlg = wx.FileDialog(self,self.rootdir,style=wx.OPEN,wildcard=filters)

        if dlg.ShowModal() == wx.ID_OK:
            self.img = dlg.GetPath()
            
            if self.width == 0:#want to do only first time
                self.width = self.panel.GetSize()[0] #need it only to resize image
                self.panel.caliper.height = self.panel.GetSize()[1]
            self.playlist = PlayList(self.img)
            
            self.DisplayPlayList()
            self.DisplayImage()

    def SaveImage(self, event):
        """
        Save the modified DC as an image.
        Blit the clientdc to a memory dc. The memory dc is initialized
        to an empty bitmap. Now, we can disconnect the bitmap from the memory dc
        and save it. 
        I copy the clientDC out before getting the savefilename because
        the 'shadow' of the save dialog results in a white area on the saved image.
        """
        context = wx.ClientDC(self.panel)
        savebmp = wx.EmptyBitmap(self.imagewidth,self.imageheight)
        #convert dc to bitmap
        memdc = wx.MemoryDC()
        memdc.SelectObject(savebmp)
        memdc.Blit(0,0,self.imagewidth,self.imageheight,context,0,0)
        memdc.SelectObject(wx.NullBitmap)

        dlg = wx.FileDialog(self, "Save image as...", os.getcwd(),
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard = 'png files|*.png')
        if dlg.ShowModal() == wx.ID_OK:
            savefilename = dlg.GetPath()
        dlg.Destroy()

        if not os.path.splitext(savefilename)[1]:
            savefilename += '.png'

        savebmp.SaveFile(savefilename,wx.BITMAP_TYPE_PNG)

    def GetBmpfromPIL( self,img ):
        self.imsmall = Image.open( img, 'r')
        
        #if frame is specified, crop image
        if self.frameextent <> (0,0,0,0):
            self.imsmall = self.imsmall.crop(self.frameextent)
            self.ZOOMFRAMEON = True
        else:
            self.ZOOMFRAMEON = False
                
        self.imsmall = self.ScaleImage(self.imsmall,self.width-self.sidepanelsize,self.panel.caliper.height)
        image = apply( wx.EmptyImage, self.imsmall.size )
        image.SetData( self.imsmall.convert( "RGB").tostring() )
        return image.ConvertToBitmap() # wxBitmapFromImage(image)
#-----------------------------------------------------------------------------------------------------------

class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, -1, TITLE)
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1
#--------------------------------------------------------------------------------------------------

## write errors to a log file

#logfile = 'eepee.log'
#fsock = open(logfile,'w')
#sys.stderr = fsock
##

app = MyApp(0)
app.MainLoop()
