#!/usr/bin/env python
from __future__ import division
import os, sys
import wx,Image
from wx.lib.floatcanvas import NavCanvas, FloatCanvas
from geticons import getBitmap

#------------------------------------------------------------------------------#
ID_OPEN     =   wx.NewId() ;   ID_UNSPLIT = wx.NewId()
ID_SAVE     =   wx.NewId()
ID_EXIT     =   wx.NewId()
#-------------------------------------------------------------------------------
class MyFrame(wx.Frame):
    """The outer frame"""
    def __init__(self,parent, id,title):
        # Create frame and maximize
        wx.Frame.__init__(self, parent, id, title, pos=(0,0),
                          style = wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        # status bar 
        self.statusbar = self.CreateStatusBar()
        
        #----------------------------------------------------------------------
        # menubar
        MenuBar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(ID_OPEN, "&Open","Open file")
        file_menu.Append(ID_SAVE, "&Save","Save Image")
        file_menu.Append(ID_EXIT, "&Exit","Exit")
   
        MenuBar.Append(file_menu, "&File")
        
        self.SetMenuBar(MenuBar)
        
        #----------------------------------------------------------------------
        ## TOOLBAR
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | 
                                          wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((22,22))

        self.toolbar.AddLabelTool(ID_OPEN, 'Open',getBitmap('open')
                                             , longHelp='Open a file')
        self.toolbar.AddLabelTool(ID_SAVE, 'Save',  getBitmap('save')
                                 , longHelp='Save the image with stamped calipers')
        
        self.toolbar.AddSeparator()        
        self.toolbar.AddLabelTool(ID_EXIT, 'Exit', getBitmap("exit")
                                  , longHelp='Exit the application')
        
        self.toolbar.AddSeparator()
        self.toolbar.AddCheckLabelTool(ID_UNSPLIT, 'Toggle sidepanel',
                                  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE,
                                   wx.ART_TOOLBAR),
                                  longHelp = 'Toggle sidepanel')
        
        self.toolbar.Realize()
        
        #--------Set up Splitter and Notebook----------------------------------
        ## SPLITTER - contains drawing panel and playlist
        self.splitter = wx.SplitterWindow(self, style=wx.SP_3D)
        self.splitter.SetMinimumPaneSize(10)
        
        # The windows inside the splitter are a
        # 1. The drawing canvas - float canvas form images
        # 2. A notebook panel holding the playlist and notes
        self.canvas = DrawingCanvas(self.splitter)
        self.notebookpanel = wx.Panel(self.splitter, -1)
        
        self.nb = wx.Notebook(self.notebookpanel) # will be a panel later
        self.listbox = wx.ListBox(self.nb, -1)
        #self.listbox.Show(True)
        self.notepad = wx.TextCtrl(self.nb, -1)
        self.nb.AddPage(self.listbox, "Playlist")
        self.nb.AddPage(self.notepad, "Notes")
        
        #---- All the sizers --------------------------------------
        notebooksizer = wx.BoxSizer()
        notebooksizer.Add(self.nb, 1, wx.EXPAND)
        self.notebookpanel.SetSizer(notebooksizer)
        
        #listboxpanelsizer = wx.BoxSizer()
        #listboxpanelsizer.Add(self.listbox, 1, wx.ALL|wx.EXPAND, 0)
        #self.listboxpanel.SetSizer(listboxpanelsizer)
                
        framesizer = wx.BoxSizer()
        framesizer.Add(self.splitter, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(framesizer)
        
        #--------------------------------------------------------
        self.accepted_formats = 'Supported formats|' + \
                    '*.png;*.PNG;*.tif;*.TIF;' +\
                    '*.tiff;*.TIFF;*.jpg;*.JPG;*.jpeg;*.JPEG;' +\
                    '*.bmp;*.BMP;*.gif;*.GIF'     
        self._FGchanged = False
        self._BGchanged = False
        self.image = None
        self.timer = wx.Timer(self, -1)
        self.timeout = 0
        self.defaultSBcolor = self.statusbar.GetBackgroundColour()
        
        #-------- Bindings ----------------------------------------------------
        wx.EVT_MENU(self,  ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self,  ID_SAVE, self.OnSave)
        
        wx.EVT_MENU(self, ID_UNSPLIT, self.SplitUnSplit)
        
        wx.EVT_MENU(self,  ID_EXIT, self.OnExit)
        
        self.Bind(wx.EVT_IDLE, self.RefreshDrawing)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        
        # works only with svn version of floatcanvas
        self.canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMotion) 
        
        # Redraw canvas background on changing splitter position
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSplitReposition)
        
        # call as future event so that size can be calculated
        wx.FutureCall(1000, self.LateInit)
    
    def LateInit(self):
        self.splitter.SplitVertically(self.canvas,self.notebookpanel)
        self.splitter.SetSashPosition(self.GetSize()[0] - 160)
        self.Bind(wx.EVT_SIZE, self.OnSize)
    
    def SplitUnSplit(self, event):
        """Unsplit or resplit the splitter"""
        if self.splitter.IsSplit():
            self.splitter.Unsplit()
        else:
            self.splitter.SplitVertically(self.canvas,self.notebookpanel)
            self.splitter.SetSashPosition(self.GetSize()[0] - 160, True)
    
    def OnExit(self, event):
        """Exit the application"""
        sys.exit()
    
    
    def OnSize(self, event):
        self.splitter.SetSashPosition(self.GetSize()[0] - 120)
        if self.image:
            self._BGchanged = True
        self.Refresh()
        
    def OnSplitReposition(self, event):
        if self.image:
            self._BGchanged = True
        self.Refresh()
        
    def OnOpen(self, event):
        """Open a file, load and display it"""        
        dlg = wx.FileDialog(self,style=wx.OPEN,wildcard=self.accepted_formats)
        if dlg.ShowModal() == wx.ID_OK:
            self.filepath = dlg.GetPath()
            try:
                #open using PIL and resize image with antialias
                size = self.splitter.GetSize()
                
                pil_image = Image.open(self.filepath,'r')
                pil_image = pil_image.resize(size,Image.ANTIALIAS)
                
                self.image = apply(wx.EmptyImage, size)
                self.image.SetData(pil_image.convert("RGB").tostring())      
                
                self.canvas.DisplayImage()
            except:
                #TODO: Handle different exceptions
                self.DisplayError("Could not load file")
            
        else:
            return
    
    
    def OnSave(self, event):
        """Save image currently on canvas"""
        dlg = wx.FileDialog(self, "Save image as...", 
                            style=wx.SAVE | wx.OVERWRITE_PROMPT,
                            wildcard=self.accepted_formats)
        if dlg.ShowModal() == wx.ID_OK:
            savefilename = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # if not a valid extension (or if no extension), save as png
        # gif not supported for now
        extension  = os.path.splitext(savefilename)[1].lower()
        canvas = self.canvas.Canvas
        try:
            
            if extension in ['.tif', '.tiff']:
                canvas.SaveAsImage(savefilename, wx.BITMAP_TYPE_TIF)
            elif extension in ['.jpg', '.jpeg']:
                canvas.SaveAsImage(savefilename, wx.BITMAP_TYPE_JPEG)
            elif extension == '.bmp':
                canvas.SaveAsImage(savefilename, wx.BITMAP_TYPE_BMP)
            else:
                savefilename = os.path.splitext(savefilename)[0] + '.png'
                canvas.SaveAsImage(savefilename, wx.BITMAP_TYPE_PNG)
            
        except:
            print 'Error' # TODO: Catch specific errors and handle meaningfully
    
       
    def OnMotion(self, event):
        #print "moving"
        self.x, self.y = event.Coords
        self.statusbar.SetStatusText("%.2f, %.2f"%tuple(event.Coords))
        #self._FGchanged = True
        
    def RefreshDrawing(self, event):
        if self._BGchanged:
            self.canvas.DrawBackground()
            self._BGchanged = False
            
        if self._FGchanged:
            self.canvas.DrawForeground()
            self._FGchanged = False
        
    def DisplayError(self, message):
        """Display error message to user"""
        self.statusbar.SetBackgroundColour('RED')
        self.statusbar.SetStatusText(message)
        #self.statusbar.Refresh() # does not work on windows
        self.statusbar.ClearBackground()
        self.timer.Start(50)

    def OnTimer(self, event):
        """Handle timeout for the error message display"""
        self.timeout += 1
        if self.timeout == 25:
            self.statusbar.SetBackgroundColour(self.defaultSBcolor)#'#E0E2EB')
            self.statusbar.SetStatusText('')
            self.statusbar.Refresh()
            self.timer.Stop()
            self.timeout = 0
        
#---------------------------------------------------------------------
class DrawingCanvas(FloatCanvas.FloatCanvas):
    """A Floatcanvas object for drawing"""
    def __init__(self, parent):
        FloatCanvas.FloatCanvas.__init__(self, parent, Debug = 0)
        self.frame = wx.GetTopLevelParent(self)
        
    def DisplayImage(self):
        """Display a scaled bitmap centered on the canvas"""
        self.ClearAll()
        self.imageheight = self.frame.image.GetHeight()
        self.bg = self.AddScaledBitmap(self.frame.image,(0,0),
                                       Height=self.imageheight, Position="cc")
        self.ZoomToBB(self.bg.BoundingBox)
    
    def DrawBackground(self):
        self.ZoomToBB(self.bg.BoundingBox)
        

#----------------------------------------------------------------------    
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, "EP Viewer")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True
    
if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()