#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Tue Oct 28 21:57:09 2008

import wx
import ConfigParser
import os

class Config():
    """The configuration stored in a config file"""
    def __init__(self, configfile):
        self.parser = ConfigParser.ConfigParser()
        self.configfile = configfile
        self.setDefault()
        self.readOptions()

    def setDefault(self):
        """Initialize with default values"""
        # find path to sample files
        if os.name == 'nt':
            sampledir = 'C:\Program Files\eepee\samples'
            #sampledir = os.path.abspath(os.path.join(os.curdir, 'samples'))
        elif os.name == 'posix':
            sampledir = '/usr/local/share/eepee/samples'
        else:
            pass

        if not os.path.exists(sampledir):
            sampledir = os.path.abspath(os.curdir)
            
        self.options = {
                   'default_dir' : sampledir,
                   'caliper_width' : '1',
                   'caliper_color' : 'black',
                   'active_caliper_color' : 'red',
                   'caliper_measurement' : 'Time',
                   'doodle_width' : '1',
                   'doodle_color' : 'red',
                   'show_fullscreen_dialog' : 'True'
                   }
        

    def readOptions(self):
        try:
            self.parser.read(self.configfile)
            for key in self.options:
                self.options[key] = self.parser.get('options', key)

        except: # if file is not present or is damaged
            return # donot change defaults
            

    def writeOptions(self):
        try:
            self.parser.add_section('options')
        except:
            pass # section already exists
            
        for key in self.options:
            self.parser.set('options', key, self.options[key])

        self.parser.write(open(self.configfile, 'w'))
# begin wxGlade: extracode
# end wxGlade

class PreferenceDialog(wx.Dialog):
    def __init__(self, parent, id, title, pref_filepath):
        """options is a dictionary"""
        # begin wxGlade: PreferenceDialog.__init__
        #kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, parent, id, title)
        self.mainpanel = wx.Panel(self,-1, style=wx.SUNKEN_BORDER)
        self.dirtext = wx.StaticText(self.mainpanel, -1, "Default directory\n")
        self.direntry = wx.TextCtrl(self.mainpanel, -1, "")
        self.dirbutton = wx.Button(self.mainpanel, -1, "Choose dir...")
        self.cwidthtext = wx.StaticText(self.mainpanel, -1, "Caliper width")
        self.cwidthcombo = wx.ComboBox(self.mainpanel, -1,
                                       choices=["1", "2", "3", "4"],
                                       style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.ccolortext = wx.StaticText(self.mainpanel, -1, "Caliper color")
        self.ccolorcombo = wx.ComboBox(self.mainpanel, -1,
                                       choices=["black", "white", "red", "blue"],
                                       style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.accolortext = wx.StaticText(self.mainpanel, -1,
                                         "Active caliper color")
        self.accolorcombo = wx.ComboBox(self.mainpanel, -1,
                                        choices=["red", "black", "white", "blue"],                                       style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.measuretext = wx.StaticText(self.mainpanel, -1, "Measurement")
        self.measurementcombo = wx.ComboBox(self.mainpanel, -1, choices=["Time", "Rate", "Both", "None"], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.dwidthtext = wx.StaticText(self.mainpanel, -1, "Doodle width")
        self.dwidthcombo = wx.ComboBox(self.mainpanel, -1, choices=["1", "2", "3", "4"], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.dcolortext = wx.StaticText(self.mainpanel, -1, "Doodle color")
        self.dcolorcombo = wx.ComboBox(self.mainpanel, -1, choices=["red", "blue", "black", "white"], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN)
        self.resetbutton = wx.Button(self.mainpanel, -1, "Reset")
        self.donebutton = wx.Button(self.mainpanel, -1, "Done")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.chooseDir, self.dirbutton)
        self.Bind(wx.EVT_BUTTON, self.onReset, self.resetbutton)
        self.Bind(wx.EVT_BUTTON, self.onDone, self.donebutton)
        # end wxGlade
        
        self.filepath = pref_filepath
        self.config = Config(self.filepath)
        self.readOptions()
        self.setOptions()

    def __set_properties(self):
        # begin wxGlade: PreferenceDialog.__set_properties
        self.SetTitle("Preferences")
        self.cwidthcombo.SetSelection(0)
        self.ccolorcombo.SetSelection(-1)
        self.accolorcombo.SetSelection(-1)
        self.measurementcombo.SetSelection(-1)
        self.dwidthcombo.SetSelection(-1)
        self.dcolorcombo.SetSelection(-1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PreferenceDialog.__do_layout
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        dcolorsizer = wx.BoxSizer(wx.HORIZONTAL)
        dwidthsizer = wx.BoxSizer(wx.HORIZONTAL)
        measuresizer = wx.BoxSizer(wx.HORIZONTAL)
        accolorsizer = wx.BoxSizer(wx.HORIZONTAL)
        ccolorsizer = wx.BoxSizer(wx.HORIZONTAL)
        cwidthsizer = wx.BoxSizer(wx.HORIZONTAL)
        dirsizer = wx.BoxSizer(wx.HORIZONTAL)
        dirsizer.Add(self.dirtext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        dirsizer.Add(self.direntry, 3, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        dirsizer.Add(self.dirbutton, 3, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(dirsizer, 1, wx.EXPAND, 0)
        cwidthsizer.Add(self.cwidthtext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        cwidthsizer.Add(self.cwidthcombo, 6, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(cwidthsizer, 1, wx.EXPAND, 0)
        ccolorsizer.Add(self.ccolortext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        ccolorsizer.Add(self.ccolorcombo, 6, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(ccolorsizer, 1, wx.EXPAND, 0)
        accolorsizer.Add(self.accolortext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        accolorsizer.Add(self.accolorcombo, 6, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(accolorsizer, 1, wx.EXPAND, 0)
        measuresizer.Add(self.measuretext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        measuresizer.Add(self.measurementcombo, 6, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(measuresizer, 1, wx.EXPAND, 0)
        dwidthsizer.Add(self.dwidthtext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        dwidthsizer.Add(self.dwidthcombo, 6, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(dwidthsizer, 1, wx.EXPAND, 0)
        dcolorsizer.Add(self.dcolortext, 4, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 2)
        dcolorsizer.Add(self.dcolorcombo, 6, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(dcolorsizer, 1, wx.EXPAND, 0)
        buttonsizer.Add(self.resetbutton, 1, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        buttonsizer.Add(self.donebutton, 1, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 2)
        mainsizer.Add(buttonsizer, 1, wx.EXPAND, 0)
        self.mainpanel.SetSizer(mainsizer)
        mainsizer.Fit(self)
        self.Layout()
        # end wxGlade
        self.SetSize((400, 400))

    def readOptions(self):
        """Read stored options from a file"""
        self.config.readOptions()
        self.options = self.config.options

    def setOptions(self):
        """Set values as per given options"""
        self.direntry.SetValue(
                            self.options.get('default_dir', ''))
        self.cwidthcombo.SetStringSelection(
                            self.options.get('caliper_width', '1'))
        self.ccolorcombo.SetStringSelection(
                            self.options.get('caliper_color', 'black'))
        self.accolorcombo.SetStringSelection(
                            self.options.get('active_caliper_color', 'red'))
        self.measurementcombo.SetStringSelection(
                            self.options.get('caliper_measurement', 'Time (ms)'))
        self.dwidthcombo.SetStringSelection(
                            self.options.get('doodle_width', '1'))
        self.dcolorcombo.SetStringSelection(
                            self.options.get('doodle_color', 'red'))

    def getOptions(self):
        """Get values"""
        self.options['default_dir'] = self.direntry.GetValue()
        self.options['caliper_width'] = self.cwidthcombo.GetValue()
        self.options['caliper_color'] = self.ccolorcombo.GetValue()
        self.options['active_caliper_color'] = self.accolorcombo.GetValue()
        self.options['caliper_measurement'] = self.measurementcombo.GetValue()
        self.options['doodle_width'] = self.dwidthcombo.GetValue()
        self.options['doodle_color'] = self.dcolorcombo.GetValue()


    def chooseDir(self, event): # wxGlade: PreferenceDialog.<event_handler>
        dlg = wx.DirDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
            self.direntry.SetValue(self.path)
        
    def onReset(self, event): # wxGlade: PreferenceDialog.<event_handler>
        """Reset the options to the ones in the file"""
        self.readOptions()
        self.setOptions()

    def onDone(self, event): # wxGlade: PreferenceDialog.<event_handler>
        """Write to file and close"""
        self.getOptions()
        self.config.options = self.options
        self.config.writeOptions()
        self.Destroy()

# end of class PreferenceDialog


