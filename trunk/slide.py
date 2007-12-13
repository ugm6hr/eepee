"""
richtextctrl for making a slide object
"""

import wx.richtext

class Slide(wx.richtext.RichTextCtrl):
    """
    The slide object
    """
    def __init__(self,parent):
        wx.richtext.RichTextCtrl.__init__(self,parent,style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.title = ''
        self.text = ''
        
        self.drawSlide()
    
    def addTitle(self):
        """
        Set the input title string as
        the title for the slide
        """
        self.BeginFontSize(40)
        self.BeginBold()
        
        self.AppendText(self.title)
        
        self.EndFontSize()
        self.EndBold()
        
        
    def addText(self):
        """
        Add non-title lines after the title
        """
        self.BeginFontSize(32)
                
        self.AppendText(self.text)
        
        self.EndFontSize()
        
        
    def drawSlide(self):
        """
        draw the slide.
        Useful to refresh the slide if title or lines change        
        """
        self.addTitle()
        self.addText()
        
    
