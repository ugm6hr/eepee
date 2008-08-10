"""
html window for making a slide object
"""

import wx.html

class Slide(wx.html.HtmlWindow):
    """
    The slide object
    """
    def __init__(self,parent):
        wx.html.HtmlWindow.__init__(self,parent)
        
        self.title = ''
        self.text = ''
        
        slidepage = self.makeSlidePage()
        
        self.SetPage(slidepage)
    
    def makeSlidePage(self):
        """
        format a page in html using the 
        title and text
        HtmlWindow does not support stylesheets
        """
        pageopentag = '<html><body bgcolor=#6666FF>'
        pageclosetag = '</html></body>'
        titleopentag = "<h1 align='center'><font size='40' face='Verdana' color=#FFFF00>"
        titleclosetag = "</font></h1>"
        textopentag = "<pre><font size='32' face='Verdana' color=#FFFF00>"
        textclosetag = "</font></pre>"
        
        slidepage = ''.join([pageopentag,
                            titleopentag,
                            self.title,
                            titleclosetag,
                            textopentag,
                            self.text,
                            textclosetag])
        return slidepage
    
    def drawSlide(self):
        """
        draw the slide.
        Useful to refresh the slide if title or lines change        
        """
        #self.SetPage("") #clear the page
        slidepage = self.makeSlidePage()
        self.SetPage(slidepage)
        
    
