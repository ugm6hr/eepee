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
class NotePad(wx.Panel):
    """ Notepad to write and display notes"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.pad = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE)
            
        s = wx.BoxSizer()
        s.Add(self.pad,1,wx.EXPAND)
        self.SetSizer(s)
        
        self.frame = wx.GetTopLevelParent(self)
        self.notes = ''
        self.frame.frameextent = (0,0,0,0)
        self.frame.window.measurement.calibration = 0 
        self.frame.SetStatusText("Not Calibrated",2)
        
    def FillNote(self,imagefilename):
        """
        Fill the notebook at beginning with previously stored notes if they 
        have been stored
        """
        (w,h) = self.GetSize()# because GetSize doesnt work in init
        self.pad.SetSize((w*0.6, h*0.9)) 
        self.pad.SetPosition((w*0.2, h*0.05)) # nicely centered potrait page
        self.notefile = os.path.splitext(imagefilename)[0] + '.note'
        
        self.pad.Clear()
        if os.path.exists(self.notefile):
            self.parseNote()
            self.pad.write(self.notes)
                    
    def SaveNote(self):
        """Save the note to the file with same name as image with suffix 'note'"""
        self.notes = self.pad.GetValue()

        # if no changes to save, dont write a note
        if self.notes == '' and \
           self.frame.window.measurement.calibration == 0 and \
           self.frame.frameextent == (0,0,0,0):
               return
            
        # else save   
        fi = open(self.notefile,'w')
        fi.write('Calibration:%s\n' % (self.frame.window.measurement.calibration)) 
        fi.write('Zoomframe:%s,%s,%s,%s\n' % self.frame.frameextent)
                                              
        fi.write(self.notes)
        fi.close()
        
    def parseNote(self): 
        """
        Parse the stored note and extract the information. Notes can be a 
        multi-line entry and will be stored at the end of the file.
        Single line entries come before. All have a header of the form 
        'somestring:' followed by the data itself. Empty lines are not allowed 
        except at the end.        
        """
        
        lines_to_parse = open(self.notefile,'r').readlines()
        linecount = 0
        
        try:
            self.frame.window.measurement.calibration = float(
                                      lines_to_parse[0].lstrip('Calibration:'))
            self.parentframe.frameextent = tuple(
                                [int(x) for x in 
                                lines_to_parse[1].lstrip('Zoomframe:').split(',')])
            self.notes = ''.join(lines_to_parse[2:])
            
        #If cannot parse, dump the whole thing on the pad
        except:
            self.notes = ''.join(lines_to_parse[:])
        
        if self.frame.window.measurement.calibration != 0:
            self.frame.window.measurement.units = 'ms'
            self.frame.SetStatusText("Calibrated",2)

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

#-----------------------------------------------------------------------
#The custom window
class MainWindow(wx.Window):
    
    def __init__(self, parent, ID):
        wx.Window.__init__(self, parent, ID)
        self.frame = wx.GetTopLevelParent(self) #top level parent to set statustext
        
        # Bind mouse events
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnDoubleClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        
        # Bind key input
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp) # generates only one event per key press
        self.SetFocus() # need this to get the key events
        
        wx.EVT_PAINT(self, self.OnPaint)
        
        self.calipersonscreen = 0
        self.caliperselectedtomove = 0
        self.calipertomove = 0
        self.caliperselected = 0
        self.calibrateselected = 0
        self.zoomselected = 0
        self.cursors = [wx.CURSOR_ARROW, wx.CURSOR_SIZEWE,
                        wx.CURSOR_SIZEWE, wx.CURSOR_HAND]
        #self.bmp = None
        self.measurement = Measurement(self,-1)
        self.writeposx_old = 0
        self.writeposy_old = 0
        self.display_old = ''
        
                
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
        
        else:
            print event.GetKeyCode() #TODO : only for testing !
    
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
                
        elif self.zoomselected:
            pass
    
    def GetUserEntry(self,message):
        """Get entry from user for calibration.
        Entry must be a positive integer"""
        calib = 0
        dialog = wx.TextEntryDialog(None,\
                                   message,"Calibrate")
        if dialog.ShowModal() == wx.ID_OK:
            calibration = dialog.GetValue()
            #calibration = int(calib)/self.measurement.measurement
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

        #writeposx = (self.leftcaliper.x1 + self.rightcaliper.x1)//2
        #writeposy = self.horizbar.y1 - 15
        #dc.DrawText(self.display_old,
        #            self.writeposx_old,self.writeposy_old)
        #dc.DrawText(self.measurement.measurementdisplay,writeposx,writeposy)
        #print writeposx, writeposy, '   ', self.writeposx_old, self.writeposy_old
        #self.writeposx_old = writeposx
        #self.writeposy_old = writeposy
        #self.display_old = self.measurement.measurementdisplay
        
    
    def OnMotion(self, event):
        
        dc = wx.ClientDC(self)
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
    
    def OnRightClick(self,event):
        if self.caliperselected:
            self.CaliperRemove()
    
    def CaliperStamp(self,event=0):
        """
        Fix the calipers in place.
        caliperselected must be true and number of calipers must be 3
        """
        dc = wx.ClientDC(self)
        
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
            #self.leftcaliperoffset = pos.x - self.leftcaliper.x1
            #self.rightcaliperoffset = pos.x - self.rightcaliper.x1
        
        else:
            self.caliperselectedtomove = 0        
              
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.frame.displayimage.bmp <> None:
            memdc = wx.MemoryDC()
            memdc.SelectObject(self.frame.displayimage.bmp)
            dc.Blit(0,0,self.GetSize()[0]-self.frame.sidepanelsize,
                                        self.GetSize()[1],memdc,0,0)
            self.prevpos =wx.Point(0,0)

#----------------------------------------------------------------------
class DisplayImage():
    
    def __init__(self,parent):
        #self.filepath = ''
        self.windowwidth = 0
        self.windowheight = 0
        self.parent = parent
        self.bmp = None
        
    def GetImage(self,imagefilepath):
        self.LoadandResizeImage(imagefilepath)
        self.ConvertImagetoBmp()
        
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
        ID_FRAME    =   wx.NewId();  
        
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
        self.toolbar.AddLabelTool(ID_ABOUT   , 'About'
                                  ,  getBitmap("about")
                                  , longHelp='About Eepee')
        self.toolbar.Realize()
        
        
        ## SPLITTER - contains notebook and list
        self.splitter = wx.SplitterWindow(self, style=wx.NO_3D|wx.SP_3D)
        self.splitter.SetMinimumPaneSize(1)
        self.notebookpanel = wx.Panel(self.splitter,-1)
        self.listbox = wx.ListBox(self.splitter,-1)
        self.listbox.Show(True)
        self.splitter.SplitVertically(self.notebookpanel,self.listbox)
        self.splitter.Unsplit() #I dont know the size yet
        
        ## NOTEBOOK - contains main window and notepad
        nb = wx.Notebook(self.notebookpanel)
        
        ## Main window
        self.window = MainWindow(nb,-1)
        self.displayimage = DisplayImage(self)
        
        ## notepad
        self.notepad = NotePad(nb)
                       
        nb.AddPage(self.window, "Tracing")
        nb.AddPage(self.notepad, "Notes")
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        self.notebookpanel.SetSizer(sizer)        
        
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
        wx.EVT_CLOSE(self, self.OnClose)
        
        ## variables
        self.rootdir = '/data'  # TODO: This is only for testing
        self.sidepanelsize = 40
        #self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
        
    def Alert(self,title,msg="Undefined"):
        dlg = wx.MessageDialog(self, msg,title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def About(self, event):
        self.Alert("About",_about)
  
    def OnClose(self,event):
        self.notepad.SaveNote()
        self.Destroy()
        
    def CaliperStart(self,event):
        self.window.caliperselected = 1
        
    def Calibrate(self,event):
        self.window.caliperselected = 1
        self.window.calibrateselected = 1

    def DisplayPlayList(self):
        self.splitter.SplitVertically(self.notebookpanel,self.listbox)
        self.splitter.SetSashPosition(self.width-self.sidepanelsize, True)

        self.listbox.Clear()
        for filename in self.playlist.playlist:
            self.listbox.Append(os.path.split(filename)[1])
            
        self.listbox.SetSelection(self.playlist.nowshowing)

    def SelectNextImage(self,event):
        self.playlist.nowshowing += 1
        if self.playlist.nowshowing == len(self.playlist.playlist):
            self.playlist.nowshowing = 0
        self.listbox.SetSelection(self.playlist.nowshowing)
            
        self.displayimage.GetImage(self.playlist.playlist[self.playlist.nowshowing])
        self.BlitSelectedImage()
        
        self.notepad.FillNote(self.playlist.playlist[self.playlist.nowshowing])

    def SelectPrevImage(self,event):
        self.playlist.nowshowing -= 1
        if self.playlist.nowshowing == -1:
            self.playlist.nowshowing = len(self.playlist.playlist)-1
        self.listbox.SetSelection(self.playlist.nowshowing)
            
        self.displayimage.GetImage(self.playlist.playlist[self.playlist.nowshowing])
        self.BlitSelectedImage()
        
        self.notepad.FillNote(self.playlist.playlist[self.playlist.nowshowing])
        
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
        self.notepad.FillNote(filepath)

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
