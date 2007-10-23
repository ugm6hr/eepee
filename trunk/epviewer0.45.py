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
        
        #FileMenu = wx.Menu()
        #FileMenu.Append(ID_SELECT,"&Open image","Open an image")
        #FileMenu.Append(ID_CALIPER,"&Save image","Save the image")
        #FileMenu.AppendSeparator()
        #FileMenu.Append(ID_EXIT,"E&xit","Terminate the program")
        
        #EditMenu = wx.Menu()
        #EditMenu.Append(ID_CALIB,"&Calibrate","Calibrate time scale")
        
        #HelpMenu = wx.Menu()
        #HelpMenu.Append(ID_ABOUT,"&About","More information about this program")

        #menuBar = wx.MenuBar()
        #menuBar.Append(FileMenu, "&File");
        #menuBar.Append(EditMenu, "&Edit");
        #menuBar.Append(HelpMenu, "&Help");
        #self.SetMenuBar(menuBar)
        
        tsize = (16,16)
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        self.toolbar.AddSimpleTool(ID_SELECT,wx.Bitmap("icons/open.png", 
                                   wx.BITMAP_TYPE_PNG), "Open") 
        
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_CALIB,wx.Bitmap("icons/calibrate.png",
                                   wx.BITMAP_TYPE_PNG),"Calibrate")
        self.toolbar.AddSimpleTool(ID_CALIPER,wx.Bitmap("icons/calipers.png",
                                   wx.BITMAP_TYPE_PNG),"Caliper")
        self.toolbar.AddSimpleTool(ID_REMOVE,wx.Bitmap("icons/remove_calipers.png",
                                   wx.BITMAP_TYPE_PNG),"Remove Caliper")
        self.toolbar.AddSimpleTool(ID_STAMP,wx.Bitmap("icons/stamp_calipers.png",
                                   wx.BITMAP_TYPE_PNG),"Stamp Caliper")
        
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_PREV,wx.Bitmap("icons/previous.png",
                                   wx.BITMAP_TYPE_PNG),"Previous")
        self.toolbar.AddSimpleTool(ID_NEXT,wx.Bitmap("icons/next.png",
                                   wx.BITMAP_TYPE_PNG),"Next")
        
        self.toolbar.AddSimpleTool(ID_SAVE,wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE,
                                   wx.ART_TOOLBAR, tsize), "Save")
        self.toolbar.AddSimpleTool(ID_EXIT,wx.ArtProvider.GetBitmap(wx.ART_QUIT,
                                   wx.ART_TOOLBAR, tsize), "Exit")

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
          
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, ID_APP, TITLE)
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1

app = MyApp(0)
app.MainLoop()

