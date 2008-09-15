#!/usr/bin/env python

from __future__ import division
import sys, os

import Image
import wx

from customrubberband import RubberBand
from geticons import getBitmap
#------------------------------------------------------------------------------
ID_OPEN     =   wx.NewId()  ;   ID_UNSPLIT = wx.NewId()
ID_SAVE     =   wx.NewId()  ;   ID_CALIPER = wx.NewId()
ID_QUIT     =   wx.NewId()  ;   #ID_ZOOMOUT = wx.NewId()
ID_CROP  =   wx.NewId()  ;   #ID_RUBBERBAND = wx.NewId()
ID_ROTATERIGHT = wx.NewId()
ID_ROTATELEFT = wx.NewId()

#last png is for default save ext
accepted_formats = ['.png', '.tiff', '.jpg', '.bmp', '.png'] 
accepted_wildcards = 'PNG|*.png|TIF|*.tif;*.tiff|' +\
                     'JPG|*.jpg;*.jpeg|BMP|*.bmp|' +\
                     'All files|*.*'
image_handlers = [wx.BITMAP_TYPE_PNG, wx.BITMAP_TYPE_TIF,
                  wx.BITMAP_TYPE_JPEG, wx.BITMAP_TYPE_BMP, wx.BITMAP_TYPE_PNG]
                  
#------------------------------------------------------------------------------
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,pos=(0,0),
                          style = wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        #--------Set up Splitter and Notebook----------------------------------
        ## SPLITTER - contains drawing panel and playlist
        ## basepanel contains the splitter  
        self.basepanel = wx.Panel(self, style=wx.SUNKEN_BORDER)
                
        self.splitter = wx.SplitterWindow(self.basepanel, style=wx.SP_3D)
        self.splitter.SetMinimumPaneSize(10)
               
        # The windows inside the splitter are a
        # 1. The drawing canvas - float canvas form images
        # 2. A notebook panel holding the playlist and notes
        self.canvas = Canvas(self.splitter)
        self.displayimage = DisplayImage(self)
        
        self.notebookpanel = wx.Panel(self.splitter, -1)
        
        self.nb = wx.Notebook(self.notebookpanel) 
        self.listbox = wx.ListBox(self.nb, -1)
        self.notepad = wx.TextCtrl(self.nb, -1)
        self.nb.AddPage(self.listbox, "Playlist")
        self.nb.AddPage(self.notepad, "Notes")

        # unsplit splitter for now, split later when size can be calculated
        self.splitter.SplitVertically(self.canvas,self.notebookpanel)
        self.splitter.Unsplit()
        
        #---- All the sizers --------------------------------------
        notebooksizer = wx.BoxSizer()
        notebooksizer.Add(self.nb, 1, wx.EXPAND, 0)
        self.notebookpanel.SetSizer(notebooksizer)
        
        splittersizer = wx.BoxSizer()
        splittersizer.Add(self.splitter, 1, wx.ALL|wx.EXPAND, 5)
        self.basepanel.SetSizer(splittersizer)
        
        #------------------------------
        self._buildMenuBar()
        self._buildToolBar()
        self.CreateStatusBar()
        
        #-------------------------------------
        self.Bind(wx.EVT_MENU, self.displayimage.LoadAndDisplayImage, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=ID_QUIT)
        self.Bind(wx.EVT_MENU, self.displayimage.SaveImage, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.ToggleSplit, id=ID_UNSPLIT)
        self.Bind(wx.EVT_MENU, self.displayimage.RotateLeft, id=ID_ROTATELEFT)
        self.Bind(wx.EVT_MENU, self.displayimage.RotateRight, id=ID_ROTATERIGHT)
        self.Bind(wx.EVT_MENU, self.displayimage.ChooseCropFrame, id=ID_CROP)
        self.Bind(wx.EVT_MENU, self.canvas.NewCaliper, id=ID_CALIPER)

    def _buildMenuBar(self):
        """Build the menu bar"""
        MenuBar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(ID_OPEN, "&Open","Open file")
        file_menu.Append(ID_SAVE, "&Save","Save Image")
        file_menu.Append(ID_QUIT, "&Exit","Exit")
   
        image_menu = wx.Menu()
        image_menu.Append(ID_ROTATELEFT, "Rotate &Left", "Rotate image left")
        image_menu.Append(ID_ROTATERIGHT, "Rotate &Right", "Rotate image right")
        
        MenuBar.Append(file_menu, "&File")
        MenuBar.Append(image_menu, "&Image")
        
        self.SetMenuBar(MenuBar)

    def _buildToolBar(self):
        """Build the toolbar"""
        ## list of tools - can be made editable in preferences
        # (checktool?, id, "short help", "long help", "getimage name")
        tools = [
            (False, ID_OPEN, "Open", "Open file", "open"),
            (False, ID_SAVE, "Save", "Save file", "save"),
            (False, ID_QUIT, "Quit", "Quit eepee", "quit"),
            (False, ID_CALIPER, "Caliper", "Start new caliper", "caliper"),
            (True,  ID_CROP, "Crop image", "Toggle cropping of image", "crop"),
            (True,  ID_UNSPLIT, "Close sidepanel", "Toggle sidepanel", "split")
            ]
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL |  wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((22,22))

        for tool in tools:
            checktool, id, shelp, lhelp, bmp = tool
            if checktool:
                self.toolbar.AddCheckLabelTool(id, shelp, getBitmap(bmp),longHelp=lhelp)
            else:
                self.toolbar.AddLabelTool(id, shelp, getBitmap(bmp),longHelp=lhelp)
                
        self.toolbar.Realize()

    def InitializeSplitter(self):
        """Initialize sash position"""
        # Do this for the first time when loading first image
        # For other images, it serves to reset sash position
        self.splitter.SplitVertically(self.canvas,self.notebookpanel)
        self.splitter.SetSashPosition(self.GetSize()[0] - 160)
    
    def ToggleSplit(self, event):
        """Unsplit or resplit the splitter"""
        if self.splitter.IsSplit():
            self.splitter.Unsplit()
        else:
            self.splitter.SplitVertically(self.canvas,self.notebookpanel)
            self.splitter.SetSashPosition(self.GetSize()[0] - 160, True)
        
        # if an image is loaded, trigger a redraw as canvas size changes
        if self.displayimage.image:
            self.canvas._BGchanged = True    
    
    def CleanUp(self):
        """Clean up on closing an image"""
        pass
    
    def OnQuit(self, event):
        """On quitting the application"""
        self.CleanUp()
        sys.exit(0)
        
#------------------------------------------------------------------------------    
class Canvas(wx.Window):
    def __init__(self, parent):
        wx.Window.__init__(self, parent, -1)
        self.SetBackgroundColour('white')
        self.frame = wx.GetTopLevelParent(self)
                
        self.rubberband = RubberBand(self)
        # Image height will always be 1000 units unless zoomed in
        self.maxheight = 1000
        
        #one tool may be active at any time
        self.activetool = None
        
        # caliper list is a list of all calipers
        self.caliperlist = []
        
        self._BGchanged = False
        self._FGchanged = False
        
        #self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)

    def OnMotion(self, event):
        pos = event.GetPosition()
        worldx, worldy = (self.PixelsToWorld(pos.x, 'xaxis'),
                          self.PixelsToWorld(pos.y, 'yaxis'))
        #worldposx = (pos.x-self.xoffset)*self.factor
        #worldposy = (pos.y-self.yoffset)*self.factor
        #self.frame.SetStatusText("%s,%s" %(worldposx, worldposy))
        self.frame.SetStatusText("%s,%s  %s,%s" %(pos.x, pos.y, worldx, worldy))
        
    def OnResize(self, event):
        """canvas resize triggers bgchanged flag so that it will
        be redrawn on next idle event"""
        if self.frame.displayimage.image: # only if image is loaded
            self._BGchanged = True
        
    def OnIdle(self, event):
        """Redraw if there is a change"""
        if self._BGchanged:
            self.DrawBG()
            
        if self._FGchanged:
            self.DrawFG()
            
    def OnMouseEvents(self, event):
        """Handle mouse events depending on active tool"""
        # ----- Rubberband -------------------------------
        if self.activetool == "rubberband":
            if event.LeftUp(): # finished selecting crop extent
                cropframe = self.rubberband.getCurrentExtent()

                self.rubberband.reset()
                self.SetCursor(wx.NullCursor)
                self.activetool = None
                
                self.frame.displayimage.CropImage(cropframe, "canvas")
                
            else:
                self.rubberband.handleMouseEvents(event)
                
        if self.activetool == "caliper":
            # the active caliper is the last one on the list
            self.caliperlist[-1].handleMouseEvents(event)
                
        elif self.activetool == None: #TODO: Move to top
            if event.Moving():
                self.OnMotion(event)

    def PixelsToWorld(self, coord, axis):
        """convert from pixels to world units.
         coord is a single value and axis denoted
         axis to which it belongs (x or y)"""
        if axis == 'xaxis':
            return round((coord - self.xoffset) * self.factor)
        elif axis == 'yaxis':
            return round((coord - self.yoffset) * self.factor)
    
    def WorldToPixels(self, coord, axis):
        """convert from world units to pixels.
         coord is a single value and axis denoted
         axis to which it belongs (x or y)"""
        if axis == 'xaxis':
            return (coord / self.factor) + self.xoffset
        elif axis == 'yaxis':
            return (coord / self.factor) + self.yoffset
        
    def DrawBG(self):
        """Draw the image after resizing to best fit current size"""
        image = self.frame.displayimage.image
        self.width, self.height = self.GetSize()
        imagewidth, imageheight = image.size
        
        # What drives the scaling - height or width
        if imagewidth / imageheight > self.width / self.height:
            self.scalingvalue = self.width / imagewidth
        else:
            self.scalingvalue = self.height / imageheight
        
        # resize with antialiasing
        self.resized_width =  int(imagewidth * self.scalingvalue)
        self.resized_height = int(imageheight * self.scalingvalue)
        self.resizedimage = image.resize((self.resized_width, self.resized_height)
                                             , Image.ANTIALIAS)
        
        # factor chosen so that image ht = 1000 U
        self.factor = self.maxheight / self.resized_height
        
        # blit the image centerd in x and y axes
        self.bmp = self.ImageToBitmap(self.resizedimage)
        dc = wx.ClientDC(self)
        dc.Clear()  #clear old image if still there
        self.imagedc = wx.MemoryDC()
        self.imagedc.SelectObject(self.bmp)
        
        self.xoffset = (self.width-self.resized_width)/2
        self.yoffset = (self.height-self.resized_height)/2
        dc.Blit(self.xoffset, self.yoffset,
                  self.resized_width, self.resized_height, self.imagedc, 0, 0)
        
        self._BGchanged = False
        
        
    def DrawFG(self):
        """Redraw the foreground elements"""
        #self.DrawBG() # will later avoid a full bg redraw
        dc = wx.ClientDC(self)
        dc.Blit(self.xoffset, self.yoffset,
                  self.resized_width, self.resized_height, self.imagedc, 0, 0)
        
        for caliper in self.caliperlist:
            caliper.draw()
            
        self._FGchanged = False
    
    def resetFG(self):
        """When the coords are not preserved, reset all
        foreground elements to default"""
        pass
        
    def ImageToBitmap(self, img):
        newimage = apply(wx.EmptyImage, img.size)
        newimage.SetData(img.convert( "RGB").tostring())
        bmp = newimage.ConvertToBitmap()
        return bmp
    
    def NewCaliper(self, event):
        """Start a new caliper"""
        self.caliperlist.append(Caliper(self))
        self.activetool = "caliper"
#------------------------------------------------------------------------------

class DisplayImage():
    """The display image and associated functions"""
    def __init__(self, parent):
        self.frame = parent
        self.canvas = self.frame.canvas
        
        self.image = None # will be loaded

        # image cropping can be toggled
        # if prev crop info is stored, this will be true
        self.iscropped = False
        
        # conversion factor to convert from px to world coords
        # = 1000 / image height in px
        self.factor = 0
        
        # keep a counter of rotation state, so that it can be saved
        self.rotation = 0
        
    def LoadAndDisplayImage(self, event):
        """Load a new image and display"""
        dlg = wx.FileDialog(self.frame ,style=wx.OPEN,
                            wildcard=accepted_wildcards)
        dlg.SetFilterIndex(4) #set 'all files' as default
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
        else:
            return
        
        try:        
            self.uncropped_image = Image.open(filepath, 'r')
        except:
            pass # TODO: catch errors and display error message
        
        if self.iscropped:
            self.image = self.CropImage(self.cropframe, "image")
        else:
            self.image = self.uncropped_image
        
        self.frame.InitializeSplitter()
        self.canvas._BGchanged = True
    
    def SaveImage(self, event):
        """
        Save the modified DC as an image.
        Initialize a memoryDC as an empty bitmap and blit the clientdc 
        to it. Then we can disconnect the bitmap from the memory dc
        and save it. 
        """
        # copy the clientDC out before getting the savefilename because
        # the 'shadow' of the save dialog results in a white area on the
        # saved image.
        # TODO: save only the image part of the screen
        context = wx.ClientDC(self.canvas)
        savebmp = wx.EmptyBitmap(self.canvas.width,self.canvas.height)
        #convert dc to bitmap
        memdc = wx.MemoryDC()
        memdc.SelectObject(savebmp)
        memdc.Blit(0,0,self.canvas.width,self.canvas.height,context,0,0)
        memdc.SelectObject(wx.NullBitmap)

        dlg = wx.FileDialog(self.frame, "Save image as...", os.getcwd(),
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard=accepted_wildcards)
        if dlg.ShowModal() == wx.ID_OK:
            savefilename = dlg.GetPath()
            filter_index = dlg.GetFilterIndex()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # format to save is dependent on selected wildcard, default to png
        savefilename += accepted_formats[filter_index]
        try:
            savebmp.SaveFile(savefilename, image_handlers[filter_index])
        except:
            pass # TODO:
    
    def RotateLeft(self, event):
        """Rotate the image 90 deg counterclockwise.
        Will reset the world coordinates"""
        self.image = self.image.transpose(Image.ROTATE_90)
        self.rotation -= 1
        self.canvas.resetFG() # since coords have changed
        self.canvas._BGchanged = True
        
    def RotateRight(self, event):
        """Rotate the image 90 deg clockwise.
        Will reset the world coordinates"""
        self.image = self.image.transpose(Image.ROTATE_270)
        self.rotation -= 1
        self.canvas.resetFG() # since coords have changed
        self.canvas._BGchanged = True
        
    def ChooseCropFrame(self, event):
        """Choose the frame to crop image using a rubberband"""
        if not self.iscropped:
            self.canvas.activetool = "rubberband"
        
        else:
            self.image = self.uncropped_image
            self.iscropped = False
            self.canvas._BGchanged = True
        
    def CropImage(self, cropframe, coord_reference):
        """Crop the image.
        crop frame is the outer frame.
        This can be in reference to the image or the canvas"""
        # convert coords to refer to image
        # for frame coords derived from canvas, first correct for image offset on canvas
        # then correct for scaling value so that coords apply to original image
        if coord_reference == "canvas":
            cropframe = (cropframe[0] - self.canvas.xoffset, cropframe[1] - self.canvas.yoffset,
                                  cropframe[2] - self.canvas.xoffset, cropframe[3] - self.canvas.yoffset)
            cropframe = tuple(int(coord/self.canvas.scalingvalue) for coord in cropframe)
            
        self.image = self.uncropped_image.crop(cropframe)

        self.iscropped = True
        self.canvas._BGchanged = True

#------------------------------------------------------------------------------
class Caliper():
    """Caliper is a tool with two vertical lines connected by a bridge"""
    def __init__(self, canvas):
        self.canvas = canvas
        # coordinates are in 'world coordinates'
        #          x1,y1    x2y1
        #           |       |
        #     x1,y2 |_______| x2,y2
        #           |       |
        #         x1,y3     x2,y3
        #
        
        self.x1, self.x2 = 0, 0
        self.y1, self.y2, self.y3 = 0, 0, 0
        
        self.pen = wx.Pen(wx.Colour(0, 0, 0), 1, wx.SOLID)
        
        # 1 - positioning first caliperleg, 2 - positioning second caliperleg
        # 3 - positioned both caliperlegs, 4 - repositioning whole caliper
        # cycle 1 -> 2 -> 3 -> 2 or 4 -> 3
        self.state = 1
        
    def draw(self):
        """draw the caliper on the canvas"""
        dc = wx.ClientDC(self.canvas)
        dc.BeginDrawing()
        dc.SetPen(self.pen)
        
        # convert to pixels for drawing
        x1 = self.canvas.WorldToPixels(self.x1, "xaxis")
        x2 = self.canvas.WorldToPixels(self.x2, "xaxis")
        y1 = self.canvas.WorldToPixels(self.y1, "yaxis")
        y2 = self.canvas.WorldToPixels(self.y2, "yaxis")
        y3 = self.canvas.WorldToPixels(self.y3, "yaxis")
        
        # draw the lines
        dc.DrawLine(x1, y1, x1, y3) # left vertical
        dc.DrawLine(x2, y1, x2, y3) # right vertical
        dc.DrawLine(x1, y2, x2, y2) # horiz
        
        dc.EndDrawing()
        
    def handleMouseEvents(self, event):
        """Mouse event handler when caliper is the active tool"""
        # get mouse position in world coords
        pos = event.GetPosition()
        mousex, mousey = (self.canvas.PixelsToWorld(pos.x, 'xaxis'),
                          self.canvas.PixelsToWorld(pos.y, 'yaxis'))
        # beginning - this is first caliper being positioned
        if event.Moving() and self.state == 1:
            self.x1 = self.x2 = mousex
            self.y1 = self.y2 = 0 #self.canvas.yoffset
            self.y3 = self.canvas.maxheight#PixelsToWorld(
                      #self.canvas.height - self.canvas.yoffset, 'yaxis')
            self.canvas._FGchanged = True
        
#------------------------------------------------------------------------------        
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Test")
        frame.Show(1)
        self.SetTopWindow(frame)
        return 1
#------------------------------------------------------------------------

def main():
    app = MyApp(0)
    app.MainLoop()


if __name__ == "__main__":
    main()
