try:
    import comtypes.client
except:
    pass
    
class ConverterError(Exception):
    """all exceptions related to the conversion """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

    
class Converter():
    """convert ppt or odp presentation to jpg images"""
    def __init__(self, path_to_presentation, target_folder):
        self.path_to_presentation = path_to_presentation
        self.target_folder = target_folder

    def convert(self):
        """will be implemented in the sublass"""
        pass


class Converter_MS(Converter):
    """converter using MS office"""
    def __init__(self, path_to_presentation, target_folder):
        Converter.__init__(path_to_presentation, target_folder)

    def convert(self):
        """use comtypes to communicate with MSoffice"""
        try:
            powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        except: # todo: exact exception
            raise ConverterError("Cannot start powerpoint")
        powerpoint.Visible = True # doesnt work otherwise !?
        try:
            powerpoint.Presentations.Open(self.path_to_presentation)
        except:
            raise ConverterError("Cannot open presentation")
        powerpoint.ActivePresentation.Export(self.target_folder, "JPG")
        powerpoint.Presentations[1].Close()
        powerpoint.Quit()

class Converter_OO(Converter):
    """converter using Openoffice"""
    def __init__(self, path_to_presentation, target_folder):
        Converter.__init__(path_to_presentation, target_folder)

    def convert(self):
        """use unoconv to convert """
        # copy presentation to dir
        # convert to pdf
        # use ghostscript to convert pdf to images
        # delete presentation
        pass
