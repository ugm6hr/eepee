#!/usr/bin/python
"""
An application for viewing and analyzing ECGs and EP tracings
"""

from __future__ import division
import wx, Image, os, copy
from customrubberband import RubberBand
from geticons import getBitmap

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
ID_SELECT   =   wx.NewId()
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

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.pad = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE)
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
            
            print self.parentframe.frameextent
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
        #print self.left_x, self.right_x
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
                  
        #Calipers and not calibrate, second caliper
        elif self.caliper.STATUS == "Second" and self.caliper.CALIBRATE == "False":
            self.caliper.ClickRight()
            self.frame.toolbar.EnableTool(ID_REMOVE, True)
            self.frame.toolbar.EnableTool(ID_STAMP, True)
        
        #calibrate, second
        elif self.caliper.STATUS == "Second" and  self.caliper.CALIBRATE == "True":
            dc = wx.ClientDC(self)
            self.caliper.ClickCalibrate(dc)
            self.caliper.STATUS = "None"
            self.caliper.CALIBRATE = "False"
            self.frame.SetStatusText('Calibrated',2)
            
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
        
    def CaliperStamp(self,event):
        dc = wx.ClientDC(self)
        self.caliper.Stamp(dc)
       
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

        self.toolbar.AddLabelTool(ID_SELECT  , 'Open'
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
        self.toolbar.AddCheckLabelTool(ID_FRAME   , 'Select frame'          
                                             ,  getBitmap("about")
                                             , longHelp='Select frame for zoom')
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
        
        #print dir(self.frametoggle)
        
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
        nb = wx.Notebook(self.notebookpanel)
        self.notepad = NotePad(nb)
        self.panel = CustomWindow(nb,-1)
        
        nb.AddPage(self.panel, "Tracing")
        nb.AddPage(self.notepad, "Notes")
        
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        self.notebookpanel.SetSizer(sizer)
        
        ##----------------------------------------------------------------------------##        
        
        wx.EVT_MENU(self,  ID_ABOUT,   self.About)
        wx.EVT_MENU(self,  ID_SELECT,  self.ChooseImage)
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
        
        self.RESIZE_FLAG = "TRUE"
        self.rootdir = os.getcwd()
        self.playlist = []
        self.BITMAP_FLAG = "notexists"
        self.panel.bmp = None
        self.sidepanelsize = 60 #side of the panel showing playlist
        self.IMAGE_SELECTED = "False"  #Has an image been selected yet?
        self.width = 0 #not initialized
        self.ZOOMFRAMEON = False
        
        
        self.InitializeAll()
    
    
    def SelectFrame(self,event):
        """
        Select the zoomframe using rubberband if not prev selected.
        If zoomframe is already on, unzoom now
        """
        
        #starting the rubberband
        if not self.ZOOMFRAMEON:
            
            if not self.panel.rubberband.enabled:
                self.panel.rubberband.enabled = True
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
                
                
                #toggle the frame icon to 'on' position
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
                
        #disable these icons initially
        self.toolbar.EnableTool(ID_CALIPER , False)
        self.toolbar.EnableTool(ID_CALIB   , False)
        self.toolbar.EnableTool(ID_REMOVE  , False)
        self.toolbar.EnableTool(ID_STAMP   , False)
        self.toolbar.EnableTool(ID_PREV    , False)
        self.toolbar.EnableTool(ID_NEXT    , False)
        self.toolbar.EnableTool(ID_SAVE    , False)
        self.toolbar.EnableTool(ID_FRAME   , False)
        #self.toolbar.EnableTool(ID_FRAMEON , False)
                
        
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
    
    def DisplayImage(self):
        
        #If there was an image before, save the note 
        if self.IMAGE_SELECTED == "TRUE":
            self.notepad.SaveNote()
            self.notepad.pad.Clear()
        else:
            self.IMAGE_SELECTED = "TRUE"
        
        self.notepad.FillNote(self.img)  #get notes
               
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
        
    def DisplayPlayList(self):
        self.splitter.SplitVertically(self.notebookpanel,self.list)
        self.splitter.SetSashPosition(self.width-self.sidepanelsize, True)
        self.list.Clear()
        
        for filename in self.playlist.playlist:
            self.list.Append(os.path.split(filename)[1])
            
        self.list.SetSelection(self.playlist.nowshowing)
    
    def ChooseImage(self,event):

        filters = 'Supported formats|*.png;*.PNG;*.tif;*.TIF;*.tiff;*.TIFF\
                                     *.jpg;*.JPG;*.jpeg;*.JPEG;\
                                     *.bmp;*.BMP;*.gif;*.GIF'
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
        
        #print self.frameextent
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


##----------------------------------------------------------------------------------------------------------
##Embedded icon images generated by img2py
##------------------------------------------------    
from wx import ImageFromStream, BitmapFromImage
import cStringIO, zlib

def getCalibrateData():
    return zlib.decompress(
'x\xda\x01f\x01\x99\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01\x1dIDAT8\x8d\xed\x94;O\x02A\x14\x85\xbfYV\
]\x1f\xf8@\x7f\x88o\xfd\x176\x86\x1a\x1b\x0b\xed\x0c\x86\x06\x8dRA"\x9dT\xc6\
\xc4\x84W"\x164\xb2K\x14\xd1_d\x03\xc9Z\xe8\xb5\x18wP\xa2\x05\xb8%\'\x93\xcc\
\xbd\xe7\xdesr2\xc5(eE\x08\x13V\xa8n#\xc3P\xa0\x00\t\xd30\x02\x9ce/=\x1e\xee\
\x8b8K\xdb<6J\x8c/n\xd1j\x94\x18\x8bm\xd2r\xcb\xd8\xb1\r\x9e\xdc2\xd6\xc2:m\
\xb7\x82\x9a_\xa3\xedU\x90\xb9U\x9e\xbd*\x1f\xb3+\xbc4\xab\xbcG\x97u\xc2\x93\
|\x9d\xcc\xd1\x0e\xe9|\x1dD\x10@\x10\xf4\x11Dz}.\xb5\xcbq\xb6\xa67\x829\x18\
\x9d\r\xd0\xf1}\x00\xbao>"?\x17D\xf4\x8b\x04\xfc\xc1yQ\xf7\xbf\xccDD\'\xdc?\
\xbd1I\xae2\t\xe2\xc9\x02\xd1\xc9\xa9\x9e\xe0kF_\xda\xfe\xf4\x82\xe8\x84\xaf\
\xdd\x0e\x00\xb7\x17\x87\xc4\x93\x05s\x0f\x03\x1b`\xdaq\x0c\x11\xd4\xdf\xb9\
\x81\rg&\xb48H\xb7\x97\xbe6\xdc\xa0P\x80\xa4rwC\x89\xff4\x0c\xcd\rP\xa3\xff\
\xf0\xdf\xf8\x04\xa0\x9c\x8b\xb6|\xca\xb5g\x00\x00\x00\x00IEND\xaeB`\x82nD\
\x91\x93' )

def getCalibrateBitmap():
    return BitmapFromImage(getCalibrateImage())

def getCalibrateImage():
    stream = cStringIO.StringIO(getCalibrateData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getCalipersData():
    return zlib.decompress(
'x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2" \xcc\xc1\x06$\
{;ey\x81\x14K\xb1\x93g\x08\x07\x10\xd4p\xa4t\x00\xf9W<]\x1cC,z\xf7Nq\xe4:d \
\xe2\xa2\xfe2rS\x81\xbeP\x81bS\x9eK\xf3\xea\xb2\xc5\xda{\x17L\xff\xc0\'\xa7&\
)\xbet\xe9\x8d\'\xeak/4\xf2\xff<\xf9\xfe\x83\xc6d\x87\x97\\A\x92\xaf9\x16\
\xe8\'\xcb\x1e\xcd\x9f\xb2N\xa1\xf3`\xf0K\xaf\xa5\xbf\xe23/\xf26l\xe4\xe3\
\x997w\xe6F\xbf9\xe7\x85\xa6M\x12\x156\xaa0\xaaX\xb7\xedz\xdd\xdf\xe9\x8a\
\x0ck\xf8M\x99:\xcfn<yNLR\xe8\xc0\xf3\xbfN\x0b8\xae{u10\xbc\xd33gJ\xb8\xfe\
\xfe\xee\xde\xf7\xc9\xa1.\x16!\'\x1c\xbdJ\x96\xff2\\\xc4x\xa0\xf8\xb3O\x90\
\x9fZ\x8e\xe6\xe5\x19\'e\xca>v\xa4\xfa[\xcdv\xd5\xd0\xcc\xd2\x10\xe4\xf9\x9e\
\xac\x18\xdfV\xe0a\xf8\xb5&e\xc6\xee\xd5;\x7fj$\x9e\\=iV\xf4;\xf9sW\xc5\xf3\
\xbdSU\xe5k\x9a\x84\x80\xfec\xf0t\xf5sY\xe7\x94\xd0\x04\x00\xbf\xbfo<' )

def getCalipersBitmap():
    return BitmapFromImage(getCalipersImage())

def getCalipersImage():
    stream = cStringIO.StringIO(getCalipersData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getRemoveCalipersData():
    return zlib.decompress(
'x\xda\x01\xd7\x01(\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01\x8eIDAT8\x8d\x95\x93\xcf+DQ\x14\xc7?\xcfF\
\x9aX\xa8W\xac\xa4L\xb1\xc0F\x13\xd9X\xd0\x94\xa4\xd9\x18k\xb1\xf6_X\xb2\xb4\
\x9a,\xed$e!ERF\x94\xb1\xf0[3\x9ad\xb2\xc0F\xd9\xce\xd7\xe2\xde7\x9eq\xe7y\
\xf3\xad\xf7\xea\xdc{\xde\xe7|\xef\xb9\xe7\x01 x\x11\x1c\xe2PrtV&\xc5<6\x8e\
\x96 %\xb8\x10\x1c\xb9\xb7#\xe3`1+(\xd7/\xee\x0bJ\x82\x94\xc3!\x8d\x1c\n|\
\xc1\x9d`\xd7\xe5tG\x90\x17\xf81\x9d\xa5-l\xd5\xb5\x1f$\x1d\t\x1eB \r\x8cg\
\xc2\xbd\x0c\xe7V\x04\xa7A\xdc\xe2\x02z0\x01t\x08\xf6\x00F&\xb3T%RS\xf3\xf5\
\xc7,\x00\xef\x1e\x8cE\x02\xad\x86\x80\xc1\x9c\xb5\xf4\x90\xdf\xa1*\xd5`@\
\x1e\xf8\xf2`8\x82\xf1[\xfd\xa0J[B\xb9\xd0\xa5d\xd2s*\x82\x04\xd7\xb1A!i\xbb\
\'\xa9[\x03H\x01*\'\xdau\xd9\xe0\x82\xfe\x85Mg\x17\x85\x81-\x08\xce\x04\xe5]\
\xd0\xcc\xfc\xd2\x9f\xcb\t\x14\xd5\xc3\xb0n0=m]\x81Z/]\xf2\xa2\x1c\xda\xd7&0\
\x8e\xe9Y\'\xd0\xe5Ao\x8c\xef\xff\x02\xcfm\xf3\x05\xcb\xa1*\xafW\x8ey\x8c\
\x94\x0f*\x18\xd8V\xfd\x1fc\xe7\xef\xac\xd4\x0c\xf4\xc4\x02\x1bZ\x07\xff\x19\
\xb4\xfe\x1f\xd0V\x7f;\x8eQY\xd0_\xf9\x19\xa7\x86I\x87\x1f ?\xe6Q\xe6@\xf7\
\x06\x9av\xc1\x1e\x05\x0749\xb4\x1b\x06\xf8\xf4\xcb\xa9]x\xfd\t\x9b\x92\x04E\
\xc1\xbd \x11\x0c\xf6\x87\x07\xddM\x82j\xf2\xa0\x0f\xf8\x04\xd6\xbe\x01\xb1\
\x1f\xc3\x0b"\xef\xa5\xf2\x00\x00\x00\x00IEND\xaeB`\x82\x93L\xce\x0e' )

def getRemoveCalipersBitmap():
    return BitmapFromImage(getRemoveCalipersImage())

def getRemoveCalipersImage():
    stream = cStringIO.StringIO(getRemoveCalipersData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getStampCalipersData():
    return zlib.decompress(
'x\xda\x01l\x01\x93\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01#IDAT8\x8d\x95T1n\xc30\x0c<R\xfd\x84\xe7\
\x16\xf0\x98\xcdS>`\x9b\xcf\xe8\x07\xfa\x82\xa0[\xb7\xa2{\xbf\x91\xe4\x03\
\x99\xb2e\x0c\x90\xceyE\xc2\x0e\x8d\x0cA"eW\x00\x07Q\xc7#y\xa2D\xc4\x01\xb5\
\xf5\xfa\xb6\xd1\xeb\xf98\xed\x9b\xb6\xc3\xf7\xe7;y\xf8\xa7*\x1b\x80\xeb\xf9\
\x88\xedn?\x11\x8c\x80\xd6\xf0<G\xd8\xb4\x1d\xc6\xa1W\x00\x18\x87^\x9b\xb6\
\xab\x07\x10\x87E&"\xba\x08[\xd3P\xef7\xb7=\xe2`\xeah\x12\xd6\x88\xe6\x88\
\x0b\xc2\x94\x8c8\xd08\xf4\xfa\xbcZ\xe3\xe7t\xc0\xcbj\x8d\xcb\xe9\x80\xednO9\
.\xcd0\x19\xfenPS\xdd\xa2/\xb5T\xcf<f\xaa0fL\xb3-\xd50\x8du\xc7&\x82D\x04\
\xc4\x81\xa2\x89H5\x19[\xd5\xc5\xfd\xe6\xe3\xcbL\x16\xfdf\x9c\xa5\x03\x0c\
\xad\xf2\x99\xf4bf_\xca\x7f\x17\x11\x07\xb7eox\xddv\xf1\xd00w\xce\t\xef\xe1\
\x88\x03\xb9\xbf\rq \xbd\xdf\xd4#}\x14Q\x9cq\x06(^J\x85\xac\xa8\x0eX\xf0\xf4\
\xbc\x0e<\\q\xcbQ\x97\x18\xe4\x99\x85\x07\x9c\x1f\xdbj\xdf\xc3 \xd3\xf1\x17\
\x8b2\xcdy\xcc;\xeef\x00\x00\x00\x00IEND\xaeB`\x82\xe4\xe0\xa0\xee' )

def getStampCalipersBitmap():
    return BitmapFromImage(getStampCalipersImage())

def getStampCalipersImage():
    stream = cStringIO.StringIO(getStampCalipersData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getNextData():
    return zlib.decompress(
'x\xda\x01j\x01\x95\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01!IDAT8\x8dc```\x10`\xa02\xf8\x0f\xc52T3p\
\xd6\xbcU0Ca\x98l\xc0\x085\x90\xe1\xe7\xaf\xdf\x0c?\x7f\xfdb\xf8\xf9\xeb\x17\
CuI:\xb2<I\x80\t\x9b`m\xeb\x14\x86\xb2\xfa>\x06\x062\\\x8ca\xe0\x7f$\xed\xf9\
\x95\x1d\x0c\x19E\xcd$\x19\x8cd n\xf5\x899\xb5\x0c\x91i\xe5\xf8\x15as!\xc2u\
\xa8\xfa`\xbc\xa0\x84"\x18\x17\xa7\xc1p\x03\xb1\xaa\xf8\xcf\xc0\xf0\x1fY\xe6\
?\x03\x83wd\x0e\x83Kp\x1aN\x83\x99\x90\x15\x13\x06\x08E6\xbe\x89\x0c\xa6n\
\xd1\x18\x063\xa1*Cu\r\x8a\x1d\xff\xd1\x99\x10R\xcf!\x94A\xdd\xca\x1fn0\x0bn\
\xb7`w2z0_:\xb0\x1a&\xc2\xc8\xc0\xc0\xc0\xc0\x82n;\x03\x03j\xd2\xc1t\x13\x04\
\x1c\xd9\xb2\x00\xc5 \x18`a\xc0P\x8a\xcfY\x0c\x0c\xdb\x96O\xc1j\x10\x9a\x81\
\xc8zq{u\xfd\xc2~\x9c\x06a5\xf0?\x9ak`1\xb3`j\x0b^W\xe1u!2\x98\xd4QI\xb4A\
\x18\x06\xfeGJ\'-5\xb9$\x1b\x84\x0c\xfe\xcf\x98\xbb\x92j\xe5!\x03\xb5\x0c\
\x81\x01\x00r(q\x82\xd2?0\xac\x00\x00\x00\x00IEND\xaeB`\x82o\x8e\x8a\xa8' )

def getNextBitmap():
    return BitmapFromImage(getNextImage())

def getNextImage():
    stream = cStringIO.StringIO(getNextData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getPreviousData():
    return zlib.decompress(
'x\xda\x01\x81\x01~\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x018IDAT8\x8d\xad\x94\xbdJ\x03A\x14F\xcf\x86\
\xcdLJ\x1f\xc0\xde\'\xb0\xb1\x16[\xc1\x14"6\x82\x10\xadS(6ZD!\tb@\x14\x92\
\x88\x12\x0b\xf1\x0f\x11A,\x02\x82\x85\xd8\xd8\xd9\xf94\xd7"\xd98\xb3;\x93l6\
\xf9``\xf6\xde;g\xbf\x99\xb9\x0cLW3\xd3\x02\xcd\x02\xd2\x1f\x13)\x82H\xfb\
\xeaA\x00\t\'\x00qt\xdcB+\x85Vj\x90\x18\x17(\x00;\x07\'\x16\xc4TZ\xa0\x00l\
\x97+h\x9d\xff\x0f:N,\rP\xd6J\xbb\x14<\x8e\x8c\xff\x8d\x04\n\xc0\xcaF9\xb6\
\xc4\x86\xc4]\xba\x80\x02\xb0X,\xf5\xceI\xcc\x848\x1b\xc3\x0c\x85\xf1\xf8\
\xfc\xd2:Z+O\xb9GFI\x18}\xce-,\x1b7\'6FbSG2\n\xe5\x80\x00\x08~\xbf^\xf8\xf9x\
\xb4\x00>o2\xc4u\xce\x98\x07@\xf0\xdd\xbd\xe1\xf3\xb5\xe30gC\x12-#I\xa0\x05~\
\x7fj\xf3v{\x96X\xe0\x97x\x81\x16\xf8\xf9\xba1\xd6\xd6\x87\x01\x07\xe0\xbb\
\x8b\x1a\x9d\xf3\xc3\xe4\x8d8\xba(\r\x10\xfan[\x8d}N\xab{#\x0b\xb3H\x00*\xf5\
f\xef\xb5\xd1y\nJ\xb1\xb5\xb9\x9a\x11g\x83\x05\x90\xe6\xe5\xbd\x00\x92\xd5\
\xa1\x0f\xce\x1f\x91~cK\x00\xbd\xd32\x00\x00\x00\x00IEND\xaeB`\x82\x82 \x96\
\x85' )

def getPreviousBitmap():
    return BitmapFromImage(getPreviousImage())

def getPreviousImage():
    stream = cStringIO.StringIO(getPreviousData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getOpenData():
    return zlib.decompress(
'x\xda\x01\x8d\x01r\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01DIDAT8\x8d\xadUKR\xc30\x0c}Jz.`\xc7!`EW\
\xb4\x07`\xc3p\x01v\xcc\xd0\xae\xcaAX\x01\xa7\x8a\xad&baI\xb5\xf3a\\\xa6o\
\x91\xb1#\xe9\xf9=E\xe3\x105-.\x89\x95-d\xe8e.\x81\x9a\x96\xfeE\x08\x00\xbb\
\xc3w\x11\xdc\xac\xaf\xcf\xe1\x9a\x12\xceaI\xf9\x18\xe6\xe4O\xc2\xb1\xe2%\
\xe4N&\x84\x8f\x0fWU$\x86\xfd\xc7O\xb1o\xce\xaa\xae\x00\x01\xa8\xeaQ-V\x00\
\xb0;|U\x17\x88\xaa\x98\xc3f}\x93\x08\xfb\xa1\x14\x99\x17\t\x04$\x80\x80\xa0\
\x0b\x80\x00\x11\x80R4U(\x85[~\xdd\x7f\x82\x8cW\x0b,Q\x88@Z!v\x9a.DOx\xda\
\xde&\xcb\xd4\xb4$C/\x81\x19\x10\x0b[\xe2\xd4\xaf\xa0$t\xd5H\xb3\xe8c\xd3q<\
\xc95U"9W\xd1\x0b\x11\x01Q\xa6X\xe1\x84\x81Y\x0b\tE\xa3\xb2\xc6\xcc\xaa\x1e\
\xe1Dxdd\x82\x12\xa5>\xc4Y\xc7RS\xec\xfd\xe5\xde\xeb|\xb0\xdf\x9e\xef\xd0\
\x1d\x19\x1d3:\x8e\x08\xcc\xbe\x0f\xcc\x081"\xc4\x88\x8e\xa3\xbe\x8f\x9a\xcb\
\xde?W\xe8\x1f&r\xd9p\xcc\xdbt\x91(\x16\xa5e\xb3}\x1a\xa9,\xd1z(\x18}\x88\
\xe9\x98\x93\xdd\xd8\xb5\xd7\xd4\x12\xcc2]\xfa\x17\xf0\x0b\xc0o\xb8\xa8\xcd\
\xf9\xb9!\x00\x00\x00\x00IEND\xaeB`\x82\x87\x9b\xa5\xcf' )

def getOpenBitmap():
    return BitmapFromImage(getOpenImage())

def getOpenImage():
    stream = cStringIO.StringIO(getOpenData())
    return ImageFromStream(stream)
#----------------------------------------------------------------------

def getSaveData():
    return zlib.decompress(
'x\xda\x01\xd9\x02&\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x02\x90IDAT8\x8d\xad\x92\xc1K\xdb`\x18\xc6\
\x7fI\xbe|_Rk\xa7\xb5\x0cQ\x14\xc5\xcb`\xe0i8\x18x\x1b;\x08;\xef\xb4\xc3\xae\
\x03o\xf5\xbf\xf0\xbc\xfbn\xfa\x07l\xec>\x06"\xee\xd2\x81\x1e7\'\x0e+m\x93\
\xb4I\xda4\xb1\xd9A\x93\xd9\xaee\x8e\xed\x81\x10\xf8\x9e\xf7\xfb\xe5y^B\x9a\
\xa6\xdc\xe8>\xffK\xdb\xdb\xdbe \xfd\xd7ggg\xe7\x9e\x00\x90R>\x06\xc8\xd2FQ\
\xc4\xad\xe4\x13\xa5\xeb:RJ\x004M\xa3\xdf\xefo\x08@[XX\x10\x00\xdd\xa8\x8f0\
\x0c\x94Rw\x02j\x9aF\xd4\x8f\xc9&]\xd7=\xbb\x06u\xbb\x1a@\xd3\xf1\xb1,Ie\xa6\
\xf8GX&\xcf\xef\x92$\x03\x00|\xdfw\xc5\r\x19\x80\x86\xebS*Z\x94K\x85;Wn\xfb]\
zQ\x0c\xc0\xf1\xf1qO\x008\x8e\x93\x03\xd34e0\x180\x18\\\x7fu\x1cX\xd3\xb4\
\xfc\xed\xf9]\x820\x02\xe0\xec\xecL\x08\x80f\xb3\t@\xd3\xed`\x1a:I\x92puu5\
\x118\x9a\xd0\xed\x84Ye]\x00\xd4\xeb\xf5\xeb\x84\x8e\x8f\xad$q\x1c\x93$\xc9X\
H\xd6 I\x12\xa2(\xa2\xedwiyAfO\t\x80Z\xad\x96W.\x15m:\x9d\xce\x100K\x99\xa6\
\xe9Pr\xdb\xb6\xf1\x86\x81J\x00\x04A\x90W\xae\xcc\x14\x11B\xe4\x17Ge\x18F\
\xbe?\xa5\xd4MB?\xb3\x97\xc4\xed\xe1\x86\xeb\xb3\xd4\xeb\xf3\xf6\xdd\xe7\x89\
{\x1b\xa7[\t\xcb\x02\xa0P(\x10\x86!\x83A\xca\xe7\xe3o\x7f\x05\x1b\x95\x00PJ\
\x11\x86a~\xb8\xb5\xb9\xce\xd3G\xab\xb4Z-\x1c\xc7\xe1\xab\xa3\x03\xf0lc\x8d$\
Ih4\x1a\xd4\xbe\x07C\xa0\xfd]\x00\xda:\x80eYC\xe6\xfb\x8f5\xda\xed6{{{T\xabU\
Vf\xaex\xf9\xfc\t\xb6mc\x9a&\xe2\xfao\xe3\xc3\xa7/\xf9\xfcPB\xdb\xb6\x87\x80\
[\x9b\xeb\x9c\x9e\x9ertt\xc4\xe1\xe1!\x17\x17\x17\xf8\xbe\xcf\xf9\xf99A\x10P\
\xaf\xd7Y\x9a_\x03`i\xbe\xfc\x0b&DQ\x07(\x14\n\xda\xe8.z\xbd^\x9e\xc4\xb2,t]\
\'\x8ec\xc20\xc4\xf3\xbc\xb1\xfbSJ\x95t UJ\xc5\xa3f\x10\x04H)\x91Rb\x18\x06R\
JJ\xa5\x12J\xa9\xb10\x80b\xb1\xf8C\x03\x98\x9b\x9b{\xd0l6O2\xe3E\xf5\xcd\xc4\
K\x99\xf6w_\xffvV\xa9T^i\x00\xa6i\xaa\xd9\xd9\xd9\xd5\xe5\xe5\xe5\x87a\x18\
\x96\x16\x17\x17\xcd\x95\x95\x15M\xd7uL\xd3\xc4\xb2,\xcd\xb6m\x0c\xc3\xc8v\
\x98\x1e\x1c\x1c\xa4\x97\x97\x97LMM\xa5\xd3\xd3\xd3\xa9\xeb\xbax\x9ew\xf2\
\x13A\xaeQ\x1b\x03\x1d\xbb\xd1\x00\x00\x00\x00IEND\xaeB`\x82\xc3\xcdL\xf3' )

def getSaveBitmap():
    return BitmapFromImage(getSaveImage())

def getSaveImage():
    stream = cStringIO.StringIO(getSaveData())
    return ImageFromStream(stream)
#---------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------
def getAboutData():
    return zlib.decompress(
"x\xda\x011\x02\xce\xfd\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\
\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x04sBIT\x08\
\x08\x08\x08|\x08d\x88\x00\x00\x01\xe8IDAT8\x8d\xbd\xd4\xcd\x8b\x8da\x18\xc7\
\xf1\xcf\xf5<\xe7\x9c\xf12\xcc\xa8I1B\xb1@\xcc\x86\xd2\xb0\xb5\x90\x94\x15\
\x8b))\x0bQ(\x7f\xc9,f\x94,d\xc1\x02%\x0be#MM:\x8c\x9a\xa6l4^Bj\xa6\xbcdR\
\x8e\x1a\xe7\xb9-\x8e43g\xce\x1c/\xe5\xb7y\xba\xaf\xe7\xfe\xfd\xfav]w\x17\
\xffE\x03\xd7\xdb\xdfy|\x1bG\x9b\xca\xd1\xd2\xb0\xeb\x10]\x9bB\xbd\x9c\x89<$\
!\xa5$\xaf\xd7=\x1cJ`\xea!\xeb\xf6\xcf\xb3\x95Z\x06\x96V\x96\xa4l\x8d\xd0\
\x8b\x9e\x9fwg\x887\x98Bj\x84\x1d\xc5\xad\xdf \xdcwn;\xa5S\xd8-t\xa2$\xa9\
\x11\xcf\xa4tC\xed\xfb\xa8\x89\xa1/M\x1c-\x03e\x15t\x12\x9f\xa4\xf4V\xe8\x12\
\xb6I\xe9\x88\xb0\\G\xf6\x1eO\x16\xba\xf2\x96y\x1b\xf6\x05\xe9\xb3\x88\x11\
\x85{\xa2\x18\x172\xa2\x9fX/\x8c\xe9\xd9\xf9\xc2\xf4\xf8\xf7\xa5\t\xfb/P\x1d\
\xa4:8\x8d{\xbf\xea{O\xbe\x96\xaf\xde\x8c\x19\x91\nI\x905\xb5,[\x94\xeeej\
\xaeE\xe7V\x11\xfb\xd1%\xc5\xb8TL\x9a\xb8\\k\x1fX\x1ddKp\xf8\xd2\x1c\xea\xb3\
\xbd\xf2\xec\x18\x0eb\x92\xe2*\xc5\xf3\xc5X\x16'\x84\xbb\xa7\x1b\xdf\xde\x93\
!J\x07\x88\xc3\xc8\xa5tM\x9a\x1d\xf1hx\x06\xf4\x1d\x9fg[b\xca\xd8s\x82\xbc\
\xbc\x8c\xe8\x93t\xa2\xaa\x9en\x1a\xbb\xf8\xe1'9\xd5\xe1?\x08\xacDP\xaf\xe0#\
FI\xa3\xea\x1do\x7f\xfd_\x10\xd6>\xf0+\xa2`Y1N\xf6J\x8a\x97\xbeM\x06\x16\x99\
ZC\xad{\x08\x1d\xdd\xa1\xb2z\xad,\x1b\x10\xce\x0b\x07\xccn,[y\xa6\xa5eiB\x08\
\xb9d\x95\x88n\xd2\n\xc5\x0c\xc5\xf4_\x06\x16\xb3I\xc4GQ\xbe\xa3\xb1 \x9e*\
\xde\xd5\xd5\x1e\xb4\xe5h\xd6\x95ym\n\x0b\x17\xc9\x82\xe7\xd2\x9ep\xe4\xfe\
\xdcS\xcb!\xfc\xbbv4o\xe9\xb9\xfa\x01\x9f\x1e\x8eF/\xe8\xf5\xf1\x00\x00\x00\
\x00IEND\xaeB`\x82\xa2+\x02n" )

def getAboutBitmap():
    return BitmapFromImage(getAboutImage())

def getAboutImage():
    stream = cStringIO.StringIO(getAboutData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getExitData():
    return zlib.decompress(
'x\xda\x01/\x05\xd0\xfa\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x16\
\x00\x00\x00\x16\x08\x06\x00\x00\x00\xc4\xb4l;\x00\x00\x00\x04sBIT\x08\x08\
\x08\x08|\x08d\x88\x00\x00\x04\xe6IDAT8\x8d\xad\x95\xdf\x8f]U\x15\xc7?k\xef}\
\xee\xb9\xb7wf\x9a\xc1\xa9:43`M\xa5\xe9\x8c\x1d[(Z\x85\x86\x06\x84P!\x1a\x8d\
\x84\x08&\xa6&\x9a\x18\x8d6>h\x8c\xff\x04\x89<\xd0\x07\x05\xd2\xd4\xc8\x8f\
\x86\x84\xa4!\x84\x9f\x16,\xa1h\xa6\x94\xfe\x04j\x7f\xccp\xef\xdc\x99;w\xe6\
\xde\x99{\xce\xd9g\x9f\xbd}8\xd361<\xf0\xc0Jv\xf6z\xd8\xeb\xbb~}\xd7\xda\xc2\
u\x19\xe4\xf3\x91\x1e\x80\x84\x100\xd1\xba\r?\xfd\xd9o\x9f\xfc\xe6\xb7\xf6\
\xdcW\xa9T\xb4\xd2\n\xad4J+\x94(D\tZk\x04Ai\x85\x88\xa0\x95\xa0\x94\x02\x01A\
\xc8\xedjr\xf8\xf9C\x7f?\xf8\xd4_~\xed\xbdK\x0c\xc0\xbd{\x1f=p\xeb\xce={\xe7\
\x17\xda\x00(e\x10\xa5\xd7\x00\xca;w\x05Zk\xe28F\t \n\xad\x05\x11\x01\xa0\
\x1a\x9b\xdaC?\xf9\xdd\xbeF\xa3\xd1\x14\x91?+mj7\x8fn\xbc\xe5{\x8d\xe6<\xfd\
\xc4\x91\xd9@\x9ay\xd2\xcc_\xd3\xf3"\xb0i|\x80/~\xa1J\x92\x16\xa4\x162\x1bH\
\xd2@\x9aAf\x85\xdej\xc1\xccl\x93\xcd[v>,\xa2\xbf\xa4D\xe4\x86v\xbb\x1d\xd9\
\xdc_\x03L\xad\'\xcb\n2\x1bX\xe9;\x86\x06\x07x\xf8\xc7\xf7\xf0\x8d\xa9\xad\
\xb8B\xb1\x9a\\\x07L3\xae\xebVqef\xbe\x82\xa8A\x03\x84\xd6\xfc\x12c7y\xbc\
\xf7\x88+\xd3+|A\xe1\xfa(]%we\xba!\x14\xa4\x99\xc7\x17\x16+\n\xa4J\xa5b\x10\
\x11\xc4\t\x1eEg)\t\x04\x8f\x01X\xed\xe7\xa4\xa9\xc5\x87\xb21\xceY\xb6l\x1ea\
\xe2\x96\r\x9c8\xdd\xa1\x9fx\x00\xacS\x18cx\xf0\xfe\xaf`\xad\xe3\xcdc\rZ\x1d\
O\\\x89\x88"\xcdb+\xa39\x9f\x82\xa8\x12\xd89Ofs\x08\xe0\n\x98\xd82\xca\x1f\
\xf7\xff\x00\x80\xd5t\x9aS\xe7\xe6\x00\xf0\xde\x13\x88P\xd1\x08\xdf\xde1\xc2\
\xfa\xa1\x98\x7f\xbcx\x85\xa5\x1e\xe8\x1cN\x9c\xfc\x18\x9b\x97\x9cS\xa5\x01\
\xd8,%\xcd,\x95J\x95\xef\xef\x9d\x02\xe0\xa5\xd7\xces\xe4\x95\xf3x\xaf\xae\
\xb1\xa51\x97p\xe8\xf9\x0f8\xf6\xde,\x13[7\xf3\xdd\xddc8\xe79\xf1\xc1,\x8bK\
\x16\xa3\xd5u\xe0\x80&\xcf\x0b\xfa\xfd\x94\xa9\xc91&\xb7n\xe2_\xc7/s\xe8\xb9\
i\xba\xbd.>\x94\x8f+\x11\xe4N\xb88\xd3\xe7\xf0\x91\x8b\x9c<\xd3\xe0\xce]\x9b\
I\xf2\xc0B\xbb\xcb\xc0`\x85(\x8e\xae\x02+B\x10\x92\xb4\xc0Z\xcf\xf8\xd8\x08\
\x00\xd3\'?\xa1\xdd\x9eC$\xe2\xd2L\x8fC\x87O\xf3\xd6\xbbM\x96W\nDi>\xba\xd4\
\xe7\xc3\xfff\x00L|m\x18\x13+t\x1cc\xccZ\xc4"\x02bH3\x07\xa2\x18^_\x07`\xb6\
\xd1#\xcf\x03\xce9\xba\xdd%\x0e>\xf3\x1e/\xbd\xf6\x11\xce\x95\xf4\xea\xb4\
\x1b\x9c<\xdf\x01`|\xe3\x10\xeb\xea\x06\xa5\xabh\xa3\x010\x88\xc2\x07E\x96\
\x15\xa4\x19\xac\xf4\x1d\x00q\xac\xe9\'\x0emJ\x87\xa8\x88\xe0!]i\xd3\xedY2\
\x1b\x18\xaa\x97\xd1\xad$\xbe\xa4\\\x14\xa3\xd6jl\xca2\x1b2[\x90f9\x97g\x96\
\x00\x98\xdc2\xc2\x91\x97!I\x0b|\xc8\xc8lJ\x96\x05\x8a\xa0\x11\xd1\x0c\x0ein\
\x9d\x1c\x06\xe0\xec\xc7K\x88\xd6\x88\x8e\xd1Z \xf8\xb2\x14\x01!Isl\x0e\xaf\
\x1f=\x03\xc0\x0f\x1f\xd8\xc6\xddw}\x9df\xab\xcb\xc2b\xca\xca\xaa\xc3yU\xb6%\
8\x1e\xf9\xd1vv\xef\x1a\xe7\xf8\xf4\x1c\xd3\xe7\x16Q\xa6\x8a\x18\x8d6\xd1\
\xda\x1e\x89\xea\xa3C#\xb7\xfd\xd2\x15\x01D\xd3j-\xe3|\x95];\xc7\xb8\xfb\xce\
\xaf\x92Y\xa1\xd3\xe9\xe2}\xa0V3\x8c\x8e~\x99\x9f?:\xc5/\x1e))\xf9\xd8\xd3g\
\xb9x\xf9\n\xdaT\x91\xa8\x86\xeb]\xe8\xce^x\xfbi#\x08\xa2"\x82/\x10\x04D\xf1\
\xc4\xdf^%w\x81?\xfc\xe6;\xfc\xfeW\xe5\xf9\xf7\xf4%D\t;\xb6\x8d\x03p\xfa\\\
\x93\xa7^\x98\xe5\xedc\xa7\xa8\xd4\x87\xc0\x94S\xabT9\xe2F\x94\x96\xc8D\xd8\
\xb5\x91\xb9\xba\x06\xffz\xf0\x9f\xbc\xf3\x9f\x16\xf7\xec\xde\xc4\xd4\xc4\
\x06\xee\xb8\xfd&\x00^=:\xcb\x89\xb3\x1d\xde8\xd6\xa4\xb50C\\\xad\x95\x8d\
\xf3\xa5\x9d6\x91\x02%\xc6\xd9nsx}\xb4\xd0\xeeTF\n\x1f \x04DJ\x07g\xce|\xc8\
\xd9s\x17\x18\xa8W\x19\x1e\xde\x80\xc7\xd0\xeb.\xd3O\x1cqM\xb3n\xa0R.\'_\x00\
\x8aj\x1c\xb3\xd2o7\xbd\xb7\x8b\xc6\xe5\xfdO6n\xdas`\xdb\xed\xfb\xfe\xd4[\
\x9e\'\xb3\x05\xa2"D4\x88A)\x83\x0f\x8a\xce\xd2*J\x1b\xa2J\x9d\x1b\x06bP\x15\
\xc4D\x88\x8a\x88\xaa\x9aZ\xadF\xe8_\xcaO\x1d\x7f\xf6\xf1\xe0\x8b\x05\t! "C#\
7n\xdb?\xb9\xfd\x81\x87j\xd5\xa8~\xf5\xf3*\x87GA\x80@\xc9\x1e\x02\xff\'%\x87\
\x17Z\xcd\xf6\xfb\xc7\x9f9\x90%\xf3O\x86\x102\t!\\\x05\xd1\xc0\x8d@\x9dO1\
\xff\x0c\xb2\x0c\xcc\x855\xc0\xff\x01c:[\xc2\xdb:\x88\x1b\x00\x00\x00\x00IEN\
D\xaeB`\x82\x8f\x92z\x04' )

def getExitBitmap():
    return BitmapFromImage(getExitImage())

def getExitImage():
    stream = cStringIO.StringIO(getExitData())
    return ImageFromStream(stream)    
#----------------------------------------------------------------------
class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, -1, TITLE)
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1
#--------------------------------------------------------------------------------------------------

app = MyApp(0)
app.MainLoop()
