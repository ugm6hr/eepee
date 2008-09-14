#!/usr/bin/env python

from __future__ import division
import sys, copy

import Image
import wx

from customrubberband import RubberBand
#------------------------------------------------------------------------------
ID_OPEN     =   wx.NewId()  ;   ID_UNSPLIT = wx.NewId()
ID_SAVE     =   wx.NewId()  ;   #ID_ZOOMIN = wx.NewId()
ID_EXIT     =   wx.NewId()  ;   #ID_ZOOMOUT = wx.NewId()
ID_CROP  =   wx.NewId()  ;   #ID_RUBBERBAND = wx.NewId()
ID_ROTATERIGHT = wx.NewId()
ID_ROTATELEFT = wx.NewId()
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
        self.Bind(wx.EVT_MENU, self.OnQuit, id=ID_EXIT)
        self.Bind(wx.EVT_MENU, self.displayimage.SaveImage, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.ToggleSplit, id=ID_UNSPLIT)
        self.Bind(wx.EVT_MENU, self.displayimage.RotateLeft, id=ID_ROTATELEFT)
        self.Bind(wx.EVT_MENU, self.displayimage.RotateRight, id=ID_ROTATERIGHT)
        self.Bind(wx.EVT_MENU, self.displayimage.ChooseCropFrame, id=ID_CROP)

    def _buildMenuBar(self):
        """Build the menu bar"""
        MenuBar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(ID_OPEN, "&Open","Open file")
        file_menu.Append(ID_SAVE, "&Save","Save Image")
        file_menu.Append(ID_EXIT, "&Exit","Exit")
   
        image_menu = wx.Menu()
        image_menu.Append(ID_ROTATELEFT, "Rotate &Left", "Rotate image left")
        image_menu.Append(ID_ROTATERIGHT, "Rotate &Right", "Rotate image right")
        
        MenuBar.Append(file_menu, "&File")
        MenuBar.Append(image_menu, "&Image")
        
        self.SetMenuBar(MenuBar)

    def _buildToolBar(self):
        """Build the toolbar"""
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL |  wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((22,22))
        
        self.toolbar.AddCheckLabelTool(ID_UNSPLIT, 'Toggle sidepanel',
                                  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE,  wx.ART_TOOLBAR),
                                  longHelp = 'Toggle sidepanel')
        self.toolbar.AddCheckLabelTool(ID_CROP, 'Crop Image',
                                  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE,  wx.ART_TOOLBAR),
                                  longHelp = 'Toggle cropping of image')

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
        self.frame = wx.GetTopLevelParent(self)
                
        self.rubberband = RubberBand(self)
        # Image height will always be 1000 units unless zoomed in
        self.maxheight = 1000
        
        #one tool may be active at any time
        self.activetool = None
        
        self._BGchanged = False
        
        #self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
    
   
    def OnMotion(self, event):
        pos = event.GetPosition()
        #worldposx = (pos.x-self.xoffset)*self.factor
        #worldposy = (pos.y-self.yoffset)*self.factor
        #self.frame.SetStatusText("%s,%s" %(worldposx, worldposy))
        self.frame.SetStatusText("%s,%s" %(pos.x, pos.y))
        
    def OnResize(self, event):
        """canvas resize triggers bgchanged flag so that it will
        be redrawn on next idle event"""
        if self.frame.displayimage.image: # only if image is loaded
            self._BGchanged = True
        
    def OnIdle(self, event):
        """Redraw if there is a change"""
        if self._BGchanged:
            self.DrawBG()
            
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
                
        elif self.activetool == None: #TODO: Move to top
            if event.Moving():
                self.OnMotion(event)

            
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
        resized_width =  int(imagewidth * self.scalingvalue)
        resized_height = int(imageheight * self.scalingvalue)
        self.resizedimage = image.resize((resized_width, resized_height)
                                             , Image.ANTIALIAS)
        
        # factor chosen so that image ht = 1000 U
        self.factor = self.maxheight / resized_height
        
        # blit the image centerd in x and y axes
        self.bmp = self.ImageToBitmap(self.resizedimage)
        dc = wx.ClientDC(self)
        dc.Clear()  #clear old image if still there
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.bmp)
        
        self.xoffset = (self.width-resized_width)/2
        self.yoffset = (self.height-resized_height)/2
        dc.Blit(self.xoffset, self.yoffset,
                  resized_width, resized_height, memdc, 0, 0)
        
        self._BGchanged = False
    
    def resetFG(self):
        """When the coords are not preserved, reset all
        foreground elements to default"""
        pass
        
    def ImageToBitmap(self, img):
        newimage = apply(wx.EmptyImage, img.size)
        newimage.SetData(img.convert( "RGB").tostring())
        bmp = newimage.ConvertToBitmap()
        return bmp
    
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
        dlg = wx.FileDialog(self.frame ,style=wx.OPEN)
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
        memdc.Blit(0,0,self.width,self.height,context,0,0)
        memdc.SelectObject(wx.NullBitmap)

        dlg = wx.FileDialog(self.frame, "Save image as...", os.getcwd(),
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard=accepted_formats)
        if dlg.ShowModal() == wx.ID_OK:
            savefilename = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # if not a valid extension (or if no extension), save as png
        # gif not supported for now
        try:
            extension  = os.path.splitext(savefilename)[1].lower()
            if extension in ['.tif', '.tiff']:
                succeeded = savebmp.SaveFile(savefilename, wx.BITMAP_TYPE_TIF)
            elif extension in ['.jpg', '.jpeg']:
                succeeded = savebmp.SaveFile(savefilename, wx.BITMAP_TYPE_JPEG)
            elif extension == '.bmp':
                succeeded = savebmp.SaveFile(savefilename, wx.BITMAP_TYPE_BMP)
            else:
                savefilename = os.path.splitext(savefilename)[0] + '.png'
                succeeded = savebmp.SaveFile(savefilename, wx.BITMAP_TYPE_PNG)
            
            if not succeeded:
                raise Error, "Unable to save file"

        except:
            print 'Error' # TODO: Catch specific errors and handle meaningfully
    
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
            cropframe = tuple(coord/self.canvas.scalingvalue for coord in cropframe)
            
        self.image = self.uncropped_image.crop(cropframe)

        self.iscropped = True
        self.canvas._BGchanged = True
        
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
