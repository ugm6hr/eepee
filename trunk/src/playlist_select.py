#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PlayListSelector is a dialog for constructing a playlist.
A playlist is simply a list of filepaths written as rows in
a plain text file.
The selector is called as a modal dialog and can be initiated with
a base list or an empty list. """

import wx, os, sys
from geticons import getBitmap

class PlayListSelector(wx.Dialog):
    def __init__(self, parent, playlist=[]):
        """playlist_selector is a dialog for constructing the playlist.
        Can start with a list of files as pre-existing list"""
        wx.Dialog.__init__(self, parent)
        
        self.controlpanel = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|
                                    wx.TAB_TRAVERSAL)
        self.listpanel = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        
        self.playlistctrl = wx.ListCtrl(self.listpanel, -1, style=wx.LC_REPORT|
                                    wx.LC_SINGLE_SEL | wx.SUNKEN_BORDER)
        self.playlistctrl.InsertColumn(0, "Path", width=280)
        self.playlistctrl.InsertColumn(1, "Name", width=100)
        
        self.addbutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("add"))
        self.removebutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("remove"))
        self.upbutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("up"))
        self.downbutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("down"))
        self.savebutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("save"))
        self.donebutton = wx.BitmapButton(self.controlpanel, -1,
                                getBitmap("quit"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.addItem, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.removeItem, self.removebutton)
        self.Bind(wx.EVT_BUTTON, self.moveUp, self.upbutton)
        self.Bind(wx.EVT_BUTTON, self.moveDown, self.downbutton)
        self.Bind(wx.EVT_BUTTON, self.savePlaylist, self.savebutton)
        self.Bind(wx.EVT_BUTTON, self.onQuit, self.donebutton)
        
        self.playlist = playlist
        self.loadPlaylist(self.playlist)
        self.wildcard = "Playlist|*.plst"
        self.lastvisiteddir = ''
        
    def __set_properties(self):
        self.SetTitle("Playlist_selector")

        self.addbutton.SetSize(self.addbutton.GetBestSize())
        self.removebutton.SetSize(self.removebutton.GetBestSize())
        self.upbutton.SetSize(self.upbutton.GetBestSize())
        self.downbutton.SetSize(self.downbutton.GetBestSize())
        self.savebutton.SetSize(self.savebutton.GetBestSize())
        self.donebutton.SetSize(self.donebutton.GetBestSize())

    def __do_layout(self):
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        controlsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.playlistctrl, 1, wx.EXPAND, 0)
        self.listpanel.SetSizer(sizer_1)
        mainsizer.Add(self.listpanel, 5, wx.ALL|wx.EXPAND, 2)
        
        controlsizer.Add(self.addbutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.removebutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.upbutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.downbutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.savebutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.donebutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        
        self.controlpanel.SetSizer(controlsizer)
        mainsizer.Add(self.controlpanel, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|
                      wx.EXPAND, 2)
        self.SetSizer(mainsizer)
        mainsizer.Fit(self)
        self.Layout()
        self.SetSize((400, 600))

    def addItem(self, event): # wxGlade: Frame.<event_handler>
        filters = 'Supported formats|' + '*.png;*.PNG;*.tif;*.TIF;' +\
          '*.tiff;*.TIFF;*.jpg;*.JPG;*.jpeg;*.JPEG;' +\
          '*.bmp;*.BMP;*.gif;*.GIF'
        dlg = wx.FileDialog(self,style=wx.OPEN | wx.MULTIPLE,wildcard=filters,
                            defaultDir=self.lastvisiteddir)
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetPaths()
            self.lastvisiteddir = os.path.dirname(selection[0])
            self.loadPlaylist(selection)
            #for path in selection:
            #    index = self.playlistctrl.InsertStringItem(sys.maxint,path)
            #    self.playlistctrl.SetStringItem(index, 1, os.path.basename(path))
        else:
            return 
        
    def loadPlaylist(self, playlist):
        """Load an existing playlist for editing"""
        for path in playlist:
            index = self.playlistctrl.InsertStringItem(sys.maxint,path)
            self.playlistctrl.SetStringItem(index, 1, os.path.basename(path))
        
    def removeItem(self, event): # wxGlade: Frame.<event_handler>
        selection = self.playlistctrl.GetFirstSelected()
        self.playlistctrl.DeleteItem(selection)

    def moveUp(self, event): # wxGlade: Frame.<event_handler>
        selection = self.playlistctrl.GetFirstSelected()
        
        if selection == 0: # Do nothing if this is first item
            return
        
        self.moveLocation(selection, selection - 1)
        
    def moveDown(self, event): # wxGlade: Frame.<event_handler>
        selection = self.playlistctrl.GetFirstSelected()
        
        if selection == self.playlistctrl.GetItemCount() - 1: # Do nothing if last item
            return
        
        self.moveLocation(selection, selection + 1)

    def moveLocation(self, current_location, new_location):
        """Move entry in playlist to new location"""
        path = self.playlistctrl.GetItemText(current_location)
        self.playlistctrl.DeleteItem(current_location)
        
        self.playlistctrl.InsertStringItem(new_location, path)
        self.playlistctrl.SetStringItem(new_location, 1, os.path.basename(path))
        self.playlistctrl.SetItemState(new_location, wx.LIST_STATE_SELECTED,
                                       wx.LIST_STATE_SELECTED)

    def savePlaylist(self, event): # wxGlade: Frame.<event_handler>
        self.playlist = [] # start with clear list
        for index in range(self.playlistctrl.GetItemCount()):
            self.playlist.append(self.playlistctrl.GetItemText(index))
        
        dlg = wx.FileDialog(self, "Save playlist as...",
                                    style=wx.SAVE | wx.OVERWRITE_PROMPT,
                                    wildcard=self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            playlistfile = dlg.GetPath()
        else:
            return
        
        if not playlistfile.endswith('.plst'):
            playlistfile += '.plst'
                
        fi = open(playlistfile, 'w') # TODO: handle errors
        for path in self.playlist:
            fi.write('%s\n' %(path))
        fi.close()          
            
    def onQuit(self, event):
        self.Destroy()
