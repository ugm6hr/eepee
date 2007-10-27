#!/usr/bin/python
"""
An application for viewing and analyzing ECGs and EP tracings
"""

from __future__ import division
import wx, Image, os, copy
from wx.lib.imagebrowser import *

TITLE          = "EP viewer"
ABOUT          = "An application to view and analyze EP tracings \n" \
                 "Author: Raja S. \n rajajs@gmail.com"

#wx IDs
ID_APP         = wx.NewId()
ID_ABOUT       = wx.NewId()
ID_SELECT      = wx.NewId()
ID_CALIB         = wx.NewId()
ID_CALIPER        = wx.NewId()
ID_EXIT        = wx.NewId()
ID_TEXT        = wx.NewId()
ID_STAMP       = wx.NewId()
ID_REMOVE      = wx.NewId()
#ID_PLAYLIST      = wx.NewId()
ID_PREV = wx.NewId()
ID_NEXT = wx.NewId()
ID_JUMP = wx.NewId()
ID_SAVE = wx.NewId()


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
            #FIXME: handle upper case
            if eachfile.split('.')[-1] in \
               ['bmp','png','jpg','jpeg','tif','tiff']:
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
    
class NotePad(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.notes = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE,)
        
    def FillNote(self,imagefilename):
        """
        Fill the notebook at beginning
        with previously stored notes if they 
        have been stored
        """
        (w,h) = self.GetSize()#because GetSize doesnt work in init
        self.notes.SetSize(( w*0.6 ,h*0.9 )) 
        self.notes.SetPosition(( w*0.2 ,h*0.05 )) #Now I have a nicely centered potrait page
        self.notefile = '.'.join((imagefilename.split('.')[0],'note'))
        if os.path.exists(self.notefile):
            self.notes.LoadFile(self.notefile)
        else:   #else start empty
            self.notes.Clear()
            
    def SaveNote(self):
        """
        Save the note to the file with 
        same name as image with suffix 'note'
        """
        self.notes.SaveFile(self.notefile)          
        
class Caliper():
    def __init__(self):
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
            self.calibscale = int(cal)/self.distance  #multiply pixels by scale to get ms
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
                
    def MeasureDistance(self,pos):
        #print self.left_x, self.right_x
        self.distance = abs(self.left_x-self.right_x)  
        if self.units == "ms":
            self.displaydistance = self.distance*self.calibscale
        else:
            self.displaydistance = self.distance
        self.measurement = ' '.join((str(int(self.displaydistance)),self.units))
                        
#The custom window
class CustomWindow(wx.Window):
    
    def __init__(self, parent, ID):
        
        wx.Window.__init__(self, parent, ID)
        self.frame = wx.GetTopLevelParent(self) #top level parent to set statustext
        self.prevpos = wx.Point(0,0) 
        
        #Bind mouse events
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnClick)
               
        wx.EVT_PAINT(self, self.OnPaint)
        
        self.units = "pixels" #default when we start
        self.caliper = Caliper()

    def OnClick(self,event):
        
        #Calipers are on and this is the first caliper
        if self.caliper.STATUS == "First":
            dc = wx.ClientDC(self)
            self.caliper.ClickLeft(dc)
                  
        #Calipers and not calibrate, second caliper
        elif self.caliper.STATUS == "Second" and self.caliper.CALIBRATE == "False":
            self.caliper.ClickRight()
            #self.toolbar.EnableTool(ID_CALIPER, True)
            #self.toolbar.EnableTool(ID_CALIB, True)
            self.frame.toolbar.EnableTool(ID_REMOVE, True)
            self.frame.toolbar.EnableTool(ID_STAMP, True)
            #self.toolbar.EnableTool(ID_PREV, False)
            #self.toolbar.EnableTool(ID_NEXT, False)
        
        #calibrate, second
        elif self.caliper.STATUS == "Second" and  self.caliper.CALIBRATE == "True":
            dc = wx.ClientDC(self)
            self.caliper.ClickCalibrate(dc)
            
            self.caliper.STATUS = "None"
            self.caliper.CALIBRATE = "False"
            
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
        #first caliper        
        if self.caliper.STATUS == "First":
            #erase prev line
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.MoveFirst(dc,pos)
        
        #second caliper
        if self.caliper.STATUS == "Second":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.MoveSecond(dc,pos)
            self.frame.SetStatusText(self.caliper.measurement)
                    
        if self.caliper.STATUS == "Done":
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
                        
        if self.caliper.STATUS == "MoveWhole": #move both cursors and horiz
            #we are near horiz bar
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosWhole(dc,pos)
                    
        if self.caliper.STATUS == "MoveFirst":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosFirst(dc,pos)
        
            self.frame.SetStatusText(self.caliper.measurement)
                
        if self.caliper.STATUS == "MoveSecond":
            dc = wx.ClientDC(self)
            pos = event.GetPosition()
            self.caliper.RePosSecond(dc,pos)
        
            self.frame.SetStatusText(self.caliper.measurement)
            
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
                
class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):

        wx.Frame.__init__(self, parent, ID_APP, title,pos=(0,0),style =
                              wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        self.sb = wx.StatusBar(self)    #StatusBar(self)
        self.SetStatusBar(self.sb)

        self.splitter = wx.SplitterWindow(self, style=wx.NO_3D|wx.SP_3D)
        self.splitter.SetMinimumPaneSize(1)
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((20,20))

        self.toolbar.AddLabelTool(ID_SELECT, 'Open',getOpenBitmap())
        
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(ID_CALIB, 'Calibrate',getCalibrateBitmap())
        self.toolbar.AddLabelTool(ID_CALIPER, 'Caliper',getCalipersBitmap())
        self.toolbar.AddLabelTool(ID_REMOVE, 'Remove Caliper',getRemoveCalipersBitmap())
        self.toolbar.AddLabelTool(ID_STAMP, 'Stamp Caliper',getStampCalipersBitmap())

        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(ID_PREV, 'Previous',getPreviousBitmap())
        self.toolbar.AddLabelTool(ID_NEXT, 'Next',getNextBitmap())
        self.toolbar.AddLabelTool(ID_SAVE, 'Save',wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE,
                                   wx.ART_TOOLBAR))
        self.toolbar.AddLabelTool(ID_EXIT, 'Exit',wx.ArtProvider.GetBitmap(wx.ART_QUIT,
                                   wx.ART_TOOLBAR))

        self.toolbar.Realize()
        
        self.notebookpanel = wx.Panel(self.splitter,-1)
        nb = wx.Notebook(self.notebookpanel)
        self.panel = CustomWindow(nb,-1)
        self.notepad = NotePad(nb)
        
        self.list = wx.ListBox(self.splitter,-1)
        self.list.Show(True)
        
        self.splitter.SplitVertically(self.notebookpanel,self.list)
        self.splitter.Unsplit() #I dont know the size yet
        
        nb.AddPage(self.panel, "Tracing")
        nb.AddPage(self.notepad, "Notes")
        
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        self.notebookpanel.SetSizer(sizer)
        
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
        
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.JumpInList)
        
        wx.EVT_CLOSE(self, self.OnClose)
                
        self.wildcard = "PNG files (*.png)|*.png|All files (*.*)|*.*"
        self.RESIZE_FLAG = "TRUE"
        self.rootdir = os.getcwd()
        self.playlist = []
        self.BITMAP_FLAG = "notexists"
        self.panel.bmp = None
        self.sidepanelsize = 60 #side of the panel showing playlist
        
        
        self.IMAGE_SELECTED = "False"  #Has an image been selected yet?
        self.width = 0 #not initialized
        
        self.InitializeAll()
        
    def InitializeAll(self):
        
        self.panel.CALIPERFLAG = "False"
        self.panel.caliper.CALIBRATE = "False"
        self.panel.caliper.STATUS = "None"
        self.panel.caliper.CALIPERMOVE = "None"
        
        #disable these icons initially
        self.toolbar.EnableTool(ID_CALIPER, False)
        self.toolbar.EnableTool(ID_CALIB, False)
        self.toolbar.EnableTool(ID_REMOVE, False)
        self.toolbar.EnableTool(ID_STAMP, False)
        self.toolbar.EnableTool(ID_PREV, False)
        self.toolbar.EnableTool(ID_NEXT, False)

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
        self.DisplayImage(self.playlist.playlist[self.playlist.nowshowing])
        
    def NextOnList(self,event):
        self.playlist.nowshowing += 1
        if self.playlist.nowshowing > len(self.playlist.playlist)-1:
            self.playlist.nowshowing = 0  
            
        self.InitializeAll()
        self.list.SetSelection(self.playlist.nowshowing)
        self.DisplayImage(self.playlist.playlist[self.playlist.nowshowing])
  
    def JumpInList(self,event): #double clicked on playlist to 'jump'
      self.playlist.nowshowing = self.list.GetSelection()
      self.DisplayImage(self.playlist.playlist[self.playlist.nowshowing])
          
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
            ratio = width_win / width_im
        else:
            ratio = height_win / height_im
        
        im = im.resize((int(width_im*ratio),int(height_im*ratio)),Image.ANTIALIAS)
        self.imagewidth,self.imageheight = im.size  # the size as displayed
        return im
                
    def DisplayImage(self,img):
       
        self.panel.bmp = self.GetBmpfromPIL(img)
        if self.panel.bmp == None:
           return 0
        
        #If there was an image before, save the note 
        if self.IMAGE_SELECTED == "TRUE":
            self.notepad.SaveNote()
        else:
            self.IMAGE_SELECTED = "TRUE"
        
        self.rootdir = os.path.dirname(img)
        self.SetStatusText(os.path.basename(img))

        dc = wx.ClientDC(self.panel)
        dc.Clear()  #clear old image if still there
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.panel.bmp)

        dc.Blit(0,0,self.width-self.sidepanelsize, self.panel.caliper.height,memdc,0,0)
        
        self.notepad.FillNote(img)  #get notes
        
        #enable icons
        self.toolbar.EnableTool(ID_CALIPER, True)
        self.toolbar.EnableTool(ID_CALIB, True)
        self.toolbar.EnableTool(ID_PREV, True)
        self.toolbar.EnableTool(ID_NEXT, True)
        
    def DisplayPlayList(self):
        self.splitter.SplitVertically(self.notebookpanel,self.list)
        self.splitter.SetSashPosition(self.width-self.sidepanelsize, True)
        self.list.Clear()
        
        for filename in self.playlist.playlist:
            self.list.Append(os.path.split(filename)[1])
            
        self.list.SetSelection(self.playlist.nowshowing)
    
    def ChooseImage(self,event):
        dlg = ImageDialog(self,self.rootdir);
        if dlg.ShowModal() == wx.ID_OK:
            img = dlg.GetFile()
            
            if self.width == 0:#want to do only first time
                self.width = self.panel.GetSize()[0] #need it only to resize image
                self.panel.caliper.height = self.panel.GetSize()[1]
            self.playlist = PlayList(img)
            
            self.DisplayPlayList()
                            
            self.DisplayImage(img)

    def SaveImage(self, event):
        dlg = wx.FileDialog(self, "Save image as...", os.getcwd(),
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard = self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

        if not os.path.splitext(filename)[1]:
            filename = filename + '.png'

        self.savefilename = filename
        
        self.WriteImage()
        dlg.Destroy()

    def WriteImage(self):
        
        context = wx.ClientDC(self.panel)
        savebmp = wx.EmptyBitmap(self.imagewidth,self.imageheight)
        #convert dc to bitmap
        memdc = wx.MemoryDC()
        memdc.SelectObject(savebmp)
        memdc.Blit(0,0,self.imagewidth,self.imageheight,context,0,0)
        memdc.SelectObject(wx.NullBitmap)
        #save it to file
        savebmp.SaveFile(self.savefilename,wx.BITMAP_TYPE_PNG)

    def GetBmpfromPIL( self,img ):
        self.imsmall = Image.open( img, 'r')
        self.imsmall = self.ScaleImage(self.imsmall,self.width-self.sidepanelsize,self.panel.caliper.height)
        image = apply( wx.EmptyImage, self.imsmall.size )
        image.SetData( self.imsmall.convert( "RGB").tostring() )
        return image.ConvertToBitmap() # wxBitmapFromImage(image)

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
          
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, ID_APP, TITLE)
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1

app = MyApp(0)
app.MainLoop()

