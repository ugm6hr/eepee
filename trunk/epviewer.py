#!/usr/bin/python
"""
An application for viewing, analyzing and presenting ECGs and EP tracings
"""

## Imports #
from __future__ import division
import wx, Image, os, copy
from customrubberband import RubberBand
from geticons import getBitmap
from slide import Slide

try:
    import cPickle as pickle
except ImportError:
    import pickle

## Import Image plugins separately and then convince Image that is
## fully initialized - needed when compiling for windows, otherwise
## I am not able to open tiff files with the windows binaries
import PngImagePlugin
import BmpImagePlugin
import TiffImagePlugin
import GifImagePlugin
import JpegImagePlugin
Image._initialized = 2


## ------------------------------------------
_title          = "EP viewer"
_about          = """
Eepee v 0.8
An application to view, analyze and present EP tracings\n   
Author: Raja S. \n 
rajajs@gmail.com\n
License: GPL
For more information and for updates visit\n  
http:\\code.google.com\p\eepee\n"""
_version = "0.8.0"
_author = "Raja Selvaraj"

#------------------------------------------------------------------------------
class Notepad2(wx.Frame):
    """Notepad as a separate window"""
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title,
                           size=(400,600))
        panel = wx.Panel(self,-1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.pad = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE)
        vbox.Add(self.pad, 1, wx.ALL|wx.EXPAND,5)
                
        self.SetSizer(vbox)
        wx.EVT_CLOSE(self, self.OnClose)
        #wx.EVT_MENU(self, ID_EXIT, self.OnClose)
        
    def ShowNotepad(self, event):
        self.Show(True)
        
    def OnClose(self, event):
        """Hide the window on close"""
        self.Show(False)
    
    def FillNote(self, note):
        self.pad.SetValue(note)
    
    # TODO:
    def GetNote(self):
        return self.pad.GetValue()
        

#-------------------------------------------------------------------------------
class Caliper():
    """
    Caliper is a line on the panel with the 4 coordinates defined. 
    For drawing a caliper, we just draw a vertical line first.
    Next will be another vertical line and a horizontal 'bridge'
    """
    def __init__(self, parent):
        self.height = parent.GetSize()[1]
                
        #initialize pen
        self.pen =wx.Pen(wx.Colour(255, 255, 255), 1, wx.SOLID)
        self.units = "pixels"
        self.InitializePos()

    def InitializePos(self):
        self.x1 = 0; self.prev_x1 = 0
        self.x2 = 0; self.prev_x2 = 0
        self.y1 = 0; self.prev_y1 = 0
        self.y2 = 0; self.prev_y2 = 0
        
    def GetPosition(self,pos,x2):
        """
        Update position for caliper from position of event.
        x2 is 0 if the line is a vertical bar.
        for a horiz line, x2 is the x coord for the 'other' caliper
        (eg. left when the horiz bar goes with the right caliper). 
        """
        if x2 == 0:
            self.x1 = self.x2 = pos.x
            self.y1 = 0
            self.y2 = self.height
        else:
            self.x1 = pos.x
            self.x2 = x2
            self.y1 = self.y2 = pos.y
        
    def DrawCaliper(self,dc,x1,y1,x2,y2):
        """
        Common code to draw caliper.
        Used by PutCaliper and RemoveCaliper
        """
        dc.SetLogicalFunction(wx.XOR)
        dc.BeginDrawing()
        dc.SetPen(self.pen)
        dc.DrawLine(x1, x2, y1, y2)
        dc.EndDrawing()    
        
    def PutCaliper(self,dc):
        self.DrawCaliper(dc,self.x1,self.x2,self.y1,self.y2)
        # Now current positions become old
        self.prev_x1 = self.x1
        self.prev_x2 = self.x2
        self.prev_y1 = self.y1
        self.prev_y2 = self.y2
        
    def RemoveCaliper(self,dc):
        self.DrawCaliper(dc,self.prev_x1,self.prev_x2,self.prev_y1,self.prev_y2)
    
        
#--------------------------------------------------------------------------
class PlayList():
    """The list of image / slide files to show"""

    def __init__(self,filename):
        self.playlist = []
        self.nowshowing = 0   #current position in list
        # Open playlist file
        if filename.endswith('.plst'):
            self.playlistfile = filename
            self.OpenPlaylist()
        # Or an image file (already filtered at selection)
        else:
            self.MakePlayList(filename)
    
    def MakePlayList(self, filename):
        """
        Make a playlist by listing all image files in the directory beginning
        from the selected file
        """
        dirname,currentimage = os.path.split(filename)
        allfiles = os.listdir(dirname)
                
        for eachfile in allfiles:
            if os.path.splitext(eachfile)[1].lower() in [
                             '.bmp','.png','.jpg','.jpeg','.tif','.tiff','.gif']:
                   self.playlist.append(os.path.join(dirname,eachfile))
        self.playlist.sort()
        self.nowshowing = self.playlist.index(filename)
                        
    def OpenPlayList(self,event,filename):
        """open an existing playlist"""
        self.playlist = filename.read().split(os.linesep).strip()
        
#-----------------------------------------------------------------------               
class Measurement():
    """ The measurement from the calipers """
    def __init__(self,parent,id):
        self.measurement = 0
        self.units = 'pixels'
        self.calibration = 0
        self.measurementdisplay = ''
        
    def MeasureDistance(self,leftx,rightx):
        self.measurement = abs(leftx - rightx)
        if self.calibration > 0:
            self.measurement *= self.calibration
        self.measurementdisplay = ' '.join((str(int(self.measurement)),self.units))


class Doodle():
    """Doodle on the image window"""
    def __init__(self, parent):
        self.lines = [] #list of doodle coords
        self.pen =wx.Pen(wx.Colour(255, 0, 0), 2, wx.SOLID)
        self.window = parent
        
    def redrawlines(self, dc):
        """Redraw the lines in event of repaint"""
        dc.SetPen(self.pen)
        for line in self.lines: # line is a list of tuples
            for coords in line:
                dc.DrawLine(*coords)
                
    def Onleftdown(self, event):
        """Start a new line on left click"""
        self.current_line = []
        self.pos = event.GetPosition()
        
    def Onmotion(self, event, dc):
        """Draw the line"""
        if event.Dragging() and event.LeftIsDown():
            dc.BeginDrawing()
            dc.SetPen(self.pen)
            pos = event.GetPosition()
            coords = (self.pos.x, self.pos.y, pos.x, pos.y)
            self.current_line.append(coords)
            dc.DrawLine(*coords)
            self.pos = pos
            dc.EndDrawing()
    
    def Onleftup(self, event):
        """End current line"""
        self.lines.append(self.current_line)
            
    def Clear(self, event):
        self.lines = []
        self.window.OnPaint(event)
            
#-----------------------------------------------------------------------
#The custom window
class MainWindow(wx.Window):
    
    def __init__(self, parent, ID):
        wx.Window.__init__(self, parent, ID, style=wx.SUNKEN_BORDER)
        self.frame = wx.GetTopLevelParent(self) #top level parent to set statustext
        
        # Bind mouse events
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnDoubleClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        
        # Bind key input
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp) # generates only one event per key press
        self.SetFocus() # need this to get the key events
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.calipersonscreen = 0
        self.caliperselectedtomove = 0
        self.calipertomove = 0
        self.caliperselected = 0
        self.calibrateselected = 0
        self.zoomselected = 0
        self.doodleselected = 0        
        
        self.cursors = [wx.CURSOR_ARROW, wx.CURSOR_SIZEWE,
                        wx.CURSOR_SIZEWE, wx.CURSOR_HAND]

        self.measurement = Measurement(self,-1)
        self.writeposx_old = 0
        self.writeposy_old = 0
        self.display_old = ''
        
        self.leftcaliper = None
        self.rightcaliper = None
        self.horizbar = None
        
        self.doodle = Doodle(self)
        self.stampedcalipers = [] #list of stamped calipers
                
    def OnKeyUp(self,event):
        
        keycode = event.GetKeyCode()
        
        if keycode == 79: # 'o' = open
            self.frame.SelectandDisplayImage(event)

        elif keycode == 366: # '<left arrow>' = prev
            self.frame.SelectPrevImage(event)

        elif keycode == 367: # '<right arrow>' = next
            self.frame.SelectNextImage(event)
        
        elif keycode == 67: #'c'= caliperstart
            self.caliperselected = 1
        
        elif keycode == 66: #'b' = calibratestart
            self.caliperselected = 1
            self.calibrateselected = 1
          
        elif keycode == 82: #'r'= caliperremove
            self.CaliperRemove()
            
        elif keycode == 83: #'s' = caliperstamp
            if self.calipersonscreen == 3 and self.calipertomove == 0:
                self.CaliperStamp()

        elif keycode == 70: # 'f' = fullscreen mode
            self.frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
        
        elif keycode == 27: # 'Esc' = exit fullscreen
            self.frame.ShowFullScreen(False)
        
        elif keycode == 78: # 'n' = notes
            self.frame.WriteNotes()
            
        elif keycode == 68: # 'd' = doodle
            self.start_doodle(None)

        else:
            print event.GetKeyCode() #TODO : only for testing !
    
    
    def start_doodle(self, event):
        # toggle state of doodle selected
        if self.doodleselected == False:
            self.caliperselected = False
            self.calibrateselected = False
            self.doodleselected = True
        
        else:
            self.doodleselected = False
    
    def OnLeftClick(self,event):
        pos = event.GetPosition()
        dc = wx.ClientDC(self)
        
        # If calipers are selected (caliper or calibrate)
        if self.caliperselected:
            # There are no calipers.
            # Start left caliper, initialize pos
            if self.calipersonscreen == 0:
                self.leftcaliper = Caliper(self)
                self.leftcaliper.GetPosition(pos,0)
                self.leftcaliper.PutCaliper(dc)
                self.calipersonscreen = 1
                
            # There is already one caliper, so fix that and start second
            elif self.calipersonscreen == 1:
                self.rightcaliper = Caliper(self)
                self.rightcaliper.GetPosition(pos,0)
                self.rightcaliper.PutCaliper(dc)
                self.horizbar = Caliper(self)
                self.horizbar.GetPosition(pos,self.leftcaliper.x1)
                self.horizbar.PutCaliper(dc)
                self.calipersonscreen = 2
                
            # Two calipers are already there, so this click fixes second
            elif self.calipersonscreen == 2:
                self.calipersonscreen = 3       
                           
                # we want to calibrate
                if self.calibrateselected:
                    calibration = self.GetUserEntry("Enter distance in ms:")
                    
                    # handle cancel
                    if calibration == None:
                        self.CaliperRemove()
                        return
                    
                    # handle invalid entry
                    while not calibration.isdigit():
                        calibration = (self.GetUserEntry
                                      ("Please enter a positive number"))
                    
                    # get calibration
                    self.measurement.calibration = (int(calibration)/
                                                  self.measurement.measurement)                                            
                    self.measurement.units = "ms"
                    self.frame.SetStatusText("Calibrated",2)
                    self.MeasureandDisplay()                        
                    self.CaliperRemove()
                                        
            # repositioning calipers, now fix it
            elif self.calipertomove <> 0:
                self.calipertomove = 0
                self.SetCursor(wx.StockCursor(self.cursors[0]))

            # two calipers are already drawn and positioned, so hold to reposition
            elif self.calipersonscreen == 3 and self.calipertomove == 0:
                if self.caliperselectedtomove == 0:
                    pass
                else:
                    self.calipertomove = self.caliperselectedtomove
                    if self.calipertomove == 3:
                        self.leftcaliperoffset = pos.x - self.leftcaliper.x1
                        self.rightcaliperoffset = pos.x - self.rightcaliper.x1
        
        # ready to select zoomframe    
        elif self.zoomselected:
            pass
        
        # ready to doodle -
        # TODO: have to send mouse events as a whole to class
        elif self.doodleselected:
            self.doodle.Onleftdown(event)
        
    def GetUserEntry(self,message):
        """Get entry from user for calibration.
        Entry must be a positive integer"""
        calib = 0
        dialog = wx.TextEntryDialog(None,\
                                   message,"Calibrate")
        if dialog.ShowModal() == wx.ID_OK:
            calibration = dialog.GetValue()
            dialog.Destroy() 
            return calibration
        else: # On cancel
            return None
                        
    def MeasureandDisplay(self):
        dc = wx.ClientDC(self)
        dc.SetLogicalFunction(wx.XOR)
        dc.SetPen(wx.Pen(wx.Colour(0,0,0), 1, wx.SOLID))
        
        self.measurement.MeasureDistance(self.leftcaliper.x1,
                                         self.rightcaliper.x1)
        self.frame.SetStatusText(self.measurement.measurementdisplay,3)
    
    def OnMotion(self, event):
        dc = wx.ClientDC(self)
        
        if self.caliperselected:
            
            pos = event.GetPosition()
            
            # still positioning left caliper        
            if self.calipersonscreen == 1:
                self.leftcaliper.RemoveCaliper(dc)
                self.leftcaliper.GetPosition(pos,0)
                self.leftcaliper.PutCaliper(dc)
            
            # positioning right caliper
            elif self.calipersonscreen == 2:
                self.rightcaliper.RemoveCaliper(dc)
                self.rightcaliper.GetPosition(pos,0)
                self.rightcaliper.PutCaliper(dc)
                self.horizbar.RemoveCaliper(dc)
                self.horizbar.GetPosition(pos,self.leftcaliper.x1)
                self.horizbar.PutCaliper(dc)
                self.MeasureandDisplay()
                            
            # Now calipersonscreen = 3
            elif self.calipersonscreen ==3:
                # change cursor according to location
                if self.calipertomove == 0:
                    self.FindCalipertoMove(pos)
                    #set cursor accordingly
                    self.SetCursor(wx.StockCursor(self.cursors[self.caliperselectedtomove]))
                # reposition left caliper
                elif self.calipertomove == 1:
                    self.leftcaliper.RemoveCaliper(dc)
                    self.leftcaliper.GetPosition(pos,0)
                    self.leftcaliper.PutCaliper(dc)
                    self.horizbar.RemoveCaliper(dc)
                    self.horizbar.GetPosition(pos,self.rightcaliper.x1)
                    self.horizbar.PutCaliper(dc)
                    self.MeasureandDisplay()
                
                # reposition right caliper
                elif self.calipertomove == 2:
                    self.rightcaliper.RemoveCaliper(dc)
                    self.rightcaliper.GetPosition(pos,0)
                    self.rightcaliper.PutCaliper(dc)
                    self.horizbar.RemoveCaliper(dc)
                    self.horizbar.GetPosition(pos,self.leftcaliper.x1)
                    self.horizbar.PutCaliper(dc)
                    self.MeasureandDisplay()
                    
                # reposition both calipers
                elif self.calipertomove == 3:
                    self.leftcaliper.RemoveCaliper(dc)
                    self.rightcaliper.RemoveCaliper(dc)
                    self.horizbar.RemoveCaliper(dc)
                    
                    self.leftcaliper.GetPosition(pos,0)
                    self.leftcaliper.x1 -= self.leftcaliperoffset
                    self.leftcaliper.x2 -= self.leftcaliperoffset
                    
                    self.rightcaliper.GetPosition(pos,0)
                    self.rightcaliper.x1 -= self.rightcaliperoffset
                    self.rightcaliper.x2 -= self.rightcaliperoffset
                    
                    self.horizbar.GetPosition(pos,self.leftcaliper.x1)
                    self.horizbar.x1 = self.rightcaliper.x1 # and not pos.x
                    
                    self.leftcaliper.PutCaliper(dc)
                    self.rightcaliper.PutCaliper(dc)
                    self.horizbar.PutCaliper(dc)
            
        elif self.doodleselected:
            self.doodle.Onmotion(event, dc)
                
    def OnLeftUp(self, event):
        if self.doodleselected:
            self.doodle.Onleftup(event)
    
    
    def CaliperRemove(self,event=0):
        """
        Remove calipers, reset everything and clear measurement.
        event is optional. caliperselected must be true to enter here,
        but can remove imcompletely drawn caliper too.
        """
        dc = wx.ClientDC(self)
        self.leftcaliper.RemoveCaliper(dc)
        if self.calipersonscreen > 1:
            self.rightcaliper.RemoveCaliper(dc)
            self.horizbar.RemoveCaliper(dc)
        self.caliperselected = 0
        self.calibrateselected = 0
        self.calipersonscreen = 0
        self.frame.SetStatusText('',3)
        
        self.leftcaliper = None
        self.rightcaliper = None
        self.horizbar = None
    
    def OnRightClick(self,event):
        if self.caliperselected:
            self.CaliperRemove()
    
    def CaliperStamp(self,event=0):
        """
        Fix the calipers in place.
        caliperselected must be true and number of calipers must be 3
        """
        dc = wx.ClientDC(self)
        
        #store the caliper positions
        # to redraw on repaint
        self.stampedcalipers.append((
            self.leftcaliper.x1, self.leftcaliper.x2,
            self.leftcaliper.y1, self.leftcaliper.y2,
            self.rightcaliper.x1, self.rightcaliper.x2,
            self.rightcaliper.y1, self.rightcaliper.y2,
            self.horizbar.x1, self.horizbar.x2,
            self.horizbar.y1, self.horizbar.y2))
        
         
        # first draw over the calipers to remove them
        self.leftcaliper.PutCaliper(dc)
        self.rightcaliper.PutCaliper(dc)
        self.horizbar.PutCaliper(dc)
    
        # Now draw with 'copy' pen
        dc.SetLogicalFunction(wx.COPY)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1, wx.SOLID))
        self.leftcaliper.PutCaliper(dc)
        self.rightcaliper.PutCaliper(dc)
        self.horizbar.PutCaliper(dc)
        
        #Write measurement
        writeposx = (self.leftcaliper.x1 + self.rightcaliper.x1)/2
        writeposy = self.horizbar.y1 - 15
        dc.DrawText(self.measurement.measurementdisplay,writeposx,writeposy)
        
        #reset positions
        self.caliperselected = 0
        self.calibrateselected = 0
        self.calipersonscreen = 0
        self.frame.SetStatusText('',3)
        
        self.leftcaliper = None
        self.rightcaliper = None
        self.horizbar = None

    
    def OnDoubleClick(self,event):
        # check caliper to move because sometimes the first click
        # activates repositioning
        if self.calipersonscreen == 3 and self.calipertomove == 0:
            self.CaliperStamp()
        
    def FindCalipertoMove(self,pos):
        """
        Define based on click position what we want to move
        """
        onhorizbar        = (abs(pos.y-self.horizbar.y1) < 5)
        betweencalipers   = ((pos.x - self.leftcaliper.x1) *\
                             (pos.x - self.rightcaliper.x1) < 0)
        onleftcaliper     = (abs(pos.x-self.leftcaliper.x1)<5)
        onrightcaliper    = (abs(pos.x-self.rightcaliper.x1)<5)
                
        if onleftcaliper and not onhorizbar:
            self.caliperselectedtomove = 1
            
        elif onrightcaliper and not onhorizbar:
            self.caliperselectedtomove = 2
           
        elif betweencalipers and onhorizbar:
            self.caliperselectedtomove = 3
        
        else:
            self.caliperselectedtomove = 0        

    def OnPaint(self, event):
               
        dc = wx.ClientDC(self)
        dc.Clear() # force repaint
        if self.frame.displayimage.bmp <> None:
            memdc = wx.MemoryDC()
            memdc.SelectObject(self.frame.displayimage.bmp)
            dc.Blit(0,0,self.GetSize()[0]-self.frame.sidepanelsize,
                                        self.GetSize()[1],memdc,0,0)
            self.prevpos =wx.Point(0,0)
        
        #redraw stamped calipers
        ## the order for drawline is really (x1,y1,x2,y2),
        ## but  ihave somehow messed this up everywhere
        if len(self.stampedcalipers) > 0:
            for (ax1,ay1,ax2,ay2,bx1,by1,bx2,by2,cx1,cy1,cx2,cy2) in self.stampedcalipers:
                dc.DrawLine(ax1, ax2, ay1, ay2)
                dc.DrawLine(bx1, bx2, by1, by2)
                dc.DrawLine(cx1, cx2, cy1, cy2)
                
            writeposx = (ax1 + bx1)/2
            writeposy = cy2 - 15
            dc.DrawText(self.measurement.measurementdisplay,writeposx,writeposy)        
        
        # redraw current caliper
        if self.leftcaliper:
            self.leftcaliper.PutCaliper(dc)
        if self.rightcaliper:
            self.rightcaliper.PutCaliper(dc)
        if self.horizbar:
            self.horizbar.PutCaliper(dc)
            
        # redraw doodles
        self.doodle.redrawlines(dc)

#----------------------------------------------------------------------
class DisplayImage():
    
    def __init__(self,parent):
        self.windowwidth = 0
        self.windowheight = 0
        self.parent = parent
        self.bmp = None
        self.data = None
                
    def GetImage(self,imagefilepath):
        self.LoadandResizeImage(imagefilepath)
        self.ConvertImagetoBmp()
        self.parent.GetData(imagefilepath) # loads the data
        self.ProcessData()
        
    def ProcessData(self):
        """Process the data loaded by Getdata"""
        if self.data:
            try:
                self.note = self.data["note"]
                self.calibration = self.data["calibration"]
            except KeyError:
                pass
        else:
            self.note = ''
            self.calibration = 0
            
        if self.calibration != 0:
            self.parent.window.measurement.calibration = self.calibration
            self.parent.SetStatusText('Calibrated', 2)
        else:
            self.parent.SetStatusText('Not calibrated', 2)
        
    def LoadandResizeImage(self,imagefilepath):
        """Load image with PIL and resize it, preserving aspect ratio"""
        image = Image.open(imagefilepath,'r')
        imagewidth, imageheight = image.size
        
        # What drives the scaling - height or width
        if imagewidth/imageheight > self.windowwidth/self.windowheight:
            self.scalingvalue = self.windowwidth / imagewidth
        else:
            self.scalingvalue = self.windowheight / imageheight
        
        # resize
        self.resizedimage = image.resize((int(imagewidth*self.scalingvalue),
                                          int(imageheight*self.scalingvalue)),
                                          Image.ANTIALIAS)
        self.width,self.height = self.resizedimage.size            
        
    def ConvertImagetoBmp(self):
        newimage = apply(wx.EmptyImage, self.resizedimage.size)
        newimage.SetData(self.resizedimage.convert( "RGB").tostring())
        self.bmp = newimage.ConvertToBitmap()         

    def SaveImage(self, event):
        """
        Save the modified DC as an image.
        Initialize a memoryDC as an empty bitmap and blit the clientdc 
        to it. Then we can disconnect the bitmap from the memory dc
        and save it. 
        I copy the clientDC out before getting the savefilename because
        the 'shadow' of the save dialog results in a white area on the saved image.
        """
        context = wx.ClientDC(self.parent)
        savebmp = wx.EmptyBitmap(self.width,self.height)
        #convert dc to bitmap
        memdc = wx.MemoryDC()
        memdc.SelectObject(savebmp)
        memdc.Blit(0,0,self.width,self.height,context,0,0)
        memdc.SelectObject(wx.NullBitmap)

        dlg = wx.FileDialog(self.parent, "Save image as...", os.getcwd(),
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard = 'png files|*.png')
        if dlg.ShowModal() == wx.ID_OK:
            savefilename = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        if not os.path.splitext(savefilename)[1]:
            savefilename += '.png'
        savebmp.SaveFile(savefilename,wx.BITMAP_TYPE_PNG)

#-----------------------------------------------------------------------------               
class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):

        wx.Frame.__init__(self, parent, -1, title,pos=(0,0),
                          style = wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        ## wx IDs
        ID_ABOUT    =   wx.NewId();  ID_SELECT   =   wx.NewId()
        ID_CALIB    =   wx.NewId();  ID_CALIPER  =   wx.NewId()
        ID_EXIT     =   wx.NewId();  ID_TEXT     =   wx.NewId()
        ID_STAMP    =   wx.NewId();  ID_REMOVE   =   wx.NewId()
        ID_PREV     =   wx.NewId();  ID_NEXT     =   wx.NewId()
        ID_JUMP     =   wx.NewId();  ID_SAVE     =   wx.NewId()
        ID_FRAME    =   wx.NewId();  ID_DOODLE   =   wx.NewId()
        ID_CLEAR    =   wx.NewId()
        
        ## STATUSBAR
        # statusbar with 4 fields, first for toolbar status messages,
        # second  for filename, third for calibration status
        # fourth for the measurements
        self.CreateStatusBar(4)
        
        ## TOOLBAR
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | 
                                          wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((20,20))

        self.toolbar.AddLabelTool(ID_SELECT  , 'Open', getBitmap("open")
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
                                       ,  getBitmap("frame")
                                       , longHelp='Select frame for zoom')
        self.toolbar.AddLabelTool(ID_SAVE    , 'Save'
                                 ,  getBitmap("save")
                                 , longHelp='Save the image with stamped calipers')
        self.toolbar.AddLabelTool(ID_EXIT    , 'Exit'
                                  ,  getBitmap("exit")
                                  , longHelp='Exit the application')
        self.toolbar.AddSeparator()
        # TODO: icons for doodle
        self.toolbar.AddLabelTool(ID_DOODLE   , 'Doodle'
                                  ,  getBitmap("about")
                                  , longHelp='Start doodling on the image')
        self.toolbar.AddLabelTool(ID_CLEAR  , 'Clear'
                                  ,  getBitmap("about")
                                  , longHelp='Clear te doodle')

        self.toolbar.AddSeparator()        
        self.toolbar.AddLabelTool(ID_ABOUT   , 'About'
                                  ,  getBitmap("about")
                                  , longHelp='About Eepee')
        self.toolbar.Realize()
        
        
        ## SPLITTER - contains notebook and list
        self.splitter = wx.SplitterWindow(self, style=wx.NO_3D|wx.SP_3D)
        self.splitter.SetMinimumPaneSize(1)
        
        
        self.imagepanel = wx.Panel(self.splitter,-1)
        self.listbox = wx.ListBox(self.splitter,-1)
        self.listbox.Show(True)
        self.splitter.SplitVertically(self.imagepanel,self.listbox)
        self.splitter.Unsplit() #I dont know the size yet
        
        ## Main window
        self.window = MainWindow(self.imagepanel,-1)
        self.displayimage = DisplayImage(self) 
        
        ## notepad
        self.notepad2 = Notepad2(self, -1, "Notes")
        sizer = wx.BoxSizer()
        sizer.Add(self.window, 1, wx.ALL|wx.EXPAND, 10)
        self.imagepanel.SetSizer(sizer)        
        
        ## Bindings
        wx.EVT_MENU(self,  ID_EXIT,    self.OnClose)
        wx.EVT_MENU(self,  ID_CALIPER, self.CaliperStart)
        wx.EVT_MENU(self,  ID_CALIB, self.Calibrate)
        wx.EVT_MENU(self,  ID_REMOVE, self.window.CaliperRemove)
        wx.EVT_MENU(self,  ID_STAMP, self.window.CaliperStamp)
        wx.EVT_MENU(self,  ID_SELECT, self.SelectandDisplayImage)
        wx.EVT_MENU(self,  ID_PREV, self.SelectPrevImage)
        wx.EVT_MENU(self,  ID_NEXT, self.SelectNextImage)
        wx.EVT_MENU(self,  ID_SAVE,   self.displayimage.SaveImage)
        wx.EVT_MENU(self,  ID_DOODLE,   self.window.start_doodle)
        wx.EVT_MENU(self,  ID_CLEAR,   self.window.doodle.Clear)
        wx.EVT_CLOSE(self, self.OnClose)
        
        wx.EVT_LISTBOX_DCLICK(self.listbox, -1, self.JumptoImage)
        
        ## variables
        self.rootdir = '/data'  # TODO: This is only for testing
        self.sidepanelsize = 40
                
    def Alert(self,title,msg="Undefined"):
        dlg = wx.MessageDialog(self, msg,title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def About(self, event):
        self.Alert("About",_about)
  
    def OnClose(self,event):
        self.CleanUp()
        self.Destroy()
    
    def WriteNotes(self):
        self.notepad2.ShowNotepad(None)
    
    def CaliperStart(self,event):
        self.window.caliperselected = 1
        
    def Calibrate(self,event):
        self.window.caliperselected = 1
        self.window.calibrateselected = 1

    def DisplayPlayList(self):
        self.splitter.SplitVertically(self.imagepanel,self.listbox)
        self.splitter.SetSashPosition(self.width-self.sidepanelsize, True)

        self.listbox.Clear()
        for filename in self.playlist.playlist:
            self.listbox.Append(os.path.split(filename)[1])
            
        self.listbox.SetSelection(self.playlist.nowshowing)

    def SelectNextImage(self,event):
        self.CleanUp()
        self.playlist.nowshowing += 1
        if self.playlist.nowshowing == len(self.playlist.playlist):
            self.playlist.nowshowing = 0
        self.listbox.SetSelection(self.playlist.nowshowing)
            
        self.displayimage.GetImage(self.playlist.playlist[self.playlist.nowshowing])
        self.BlitSelectedImage()

    def SelectPrevImage(self,event):
        self.CleanUp()
        self.playlist.nowshowing -= 1
        if self.playlist.nowshowing == -1:
            self.playlist.nowshowing = len(self.playlist.playlist)-1
        self.listbox.SetSelection(self.playlist.nowshowing)
            
        self.displayimage.GetImage(self.playlist.playlist[self.playlist.nowshowing])
        self.BlitSelectedImage()
       
    def JumptoImage(self,event):
        """On double clicking in listbox select that image"""
        self.CleanUp()
        self.playlist.nowshowing = self.listbox.GetSelection()
        self.displayimage.GetImage(self.playlist.playlist[self.playlist.nowshowing])
        self.BlitSelectedImage()
        ## have to set focus back to window to catch keypresse
        self.window.SetFocus()
        
    def CleanUp(self):
        """Clean up prev when choosing a new image.
        Reinitialize variables and save things"""
        if self.displayimage.bmp == None: # this is first image
            pass
        
        else:
            self.SaveData()
            
            # TODO: A common variable initialization routine
            self.window.caliperselected = 0
            self.window.calipersonscreen = 0
            self.window.caliperselectedtomove = 0
            self.window.calibrateselected = 0
            self.window.zoomselected = 0
            self.window.doodleselected = 0
            self.leftcaliper = None
            self.rightcaliper = None
            self.horizbar = None
            self.window.doodle.lines = []
            self.window.stampedcalipers = []
            self.window.measurement.calibration = 0
            self.displayimage.data
            
    def SaveData(self):
        note = self.notepad2.GetNote()
        calibration = self.window.measurement.calibration
        
        # save only if there is data
        if True in [note != '', calibration != 0]:
            datadict = {"note" : note,
                        "calibration" : calibration}
            
            imagefile = self.playlist.playlist[self.playlist.nowshowing]
           
            # save as hidden file
            if os.name == 'posix':
                pklfile = os.path.dirname(imagefile) + "/." + \
                          os.path.splitext(os.path.basename(imagefile))[0] +\
                          ".pkl"
                pickle.dump(datadict, open(pklfile, 'w'))
            
            elif os.name == 'nt':
                pklfile = os.path.splitext(imagefile)[0] + ".pkl"
                pickle.dump(datadict, open(pklfile, 'w'))
                status = commands.getstatus("attrib +h %s" %(pklfile))
                if status != 0:
                    pass
                    #TODO: raise error

    def GetData(self, imagefile):
        """Read stored data if present"""
        if os.name == 'posix':
            pklfile = os.path.dirname(imagefile) + "/." + \
                          os.path.splitext(os.path.basename(imagefile))[0] +\
                          ".pkl"
        elif os.name == 'nt':
            pklfile = os.path.splitext(imagefile)[0] + ".pkl"
        
        if os.path.exists(pklfile):
                self.displayimage.data = pickle.load(open(pklfile,'r'))  
        
    def SelectandDisplayImage(self,event):
        # TODO: define rootdir
        self.width, self.height = self.window.GetSize()
        self.displayimage.windowwidth, self.displayimage.windowheight = \
                                       self.width, self.height
        filters = 'Supported formats|*.png;*.PNG;*.tif;*.TIF;*.tiff;*.TIFF\
                                     *.jpg;*.JPG;*.jpeg;*.JPEG;\
                                     *.bmp;*.BMP;*.gif;*.GIF'
        dlg = wx.FileDialog(self,self.rootdir,style=wx.OPEN,wildcard=filters)
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
        else:
            return

        self.playlist = PlayList(filepath)
        
        self.displayimage.GetImage(filepath)
        self.DisplayPlayList()
        self.BlitSelectedImage()        
        self.notepad2.FillNote(self.displayimage.note)
        
    def BlitSelectedImage(self):
        dc = wx.ClientDC(self.window)
        dc.Clear()  #clear old image if still there
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.displayimage.bmp)
        dc.Blit(0, 0, self.width-self.sidepanelsize, self.height, memdc, 0, 0)

#----------------------------------------------------------------------    
class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, -1, _title)
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1

def main():
    app = MyApp(0)
    app.MainLoop()


if __name__ == "__main__":
    main()
