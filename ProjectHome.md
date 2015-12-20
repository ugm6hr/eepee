A comprehensive suite for presenting and analyzing ECGs and EP tracings that are available as images.

Eepee is meant to provide an alternative to powerpoint as a means of presenting EP tracings. While the strength of powerpoint maybe ease of use for those accustomed to it and the ability to integrate the images with slides, the inability to dynamically make measurements is a big disability. By providing this, eepee aims to provide a more familiar environment for electrophysiologists to discuss and analyse tracings.

Read more in the wiki for InstallationInstructions and [Features](Features.md).
HowToUse is a quick introduction to using eepee.
Have a question? See if your questions is listed among the frequently asked questions at [FAQ](FAQ.md). This software is still at an early stage in development and you can help by reporting any bugs or suggestions for improvement. See the Issues section for bugs and feature requests that are already listed. This is opensource software. If you are not sure what that means and are still wondering how much this costs, read HowMuchDoesThisCost.


**Credits:**
  * Written in [Python](http://www.python.org/).
  * Almost all of the development was done on Gnu/Linux, specifically [Ubuntu](http://www.ubuntu.com/).
  * Some of the icons come from the [Tango desktop project](http://tango.freedesktop.org/Tango_Desktop_Project) and some from [Gimp](http://www.gimp.org/).
  * Windows binary compiled with [pyinstaller](http://pyinstaller.python-hosting.com/) and installer made with [Innosetup](http://www.jrsoftware.org/isinfo.php).


![http://www.python.org/community/logos/python-powered-h-50x65.png](http://www.python.org/community/logos/python-powered-h-50x65.png)     ![http://lh3.ggpht.com/rajajs/SOVZFa9w6QI/AAAAAAAABFo/I2t6WMsbFVo/s144/UbuntuLogo.png](http://lh3.ggpht.com/rajajs/SOVZFa9w6QI/AAAAAAAABFo/I2t6WMsbFVo/s144/UbuntuLogo.png)

## 02 December 2013 - Version 1.0 ##
Fixes some bugs from the previous release.
  * Saving works again on windows
  * Linux installation is fixed
  * Fixes to work with Pillow (fork of PIL)


## 16 September 2013 - Version 0.9.9 released after a long break ##
Important new features
  * Takes filename as argument when used from commandline
  * Can be used to directly open an image from 'open with' menu
  * Powerpoint imports are transparent, just open ppt file
  * Right click pops up menu with useful functions
  * Rename files directly from the playlist pane
  * 'Truncated cursor' can be chosen in preferences instead of full height cursor


## 07 July 2009. Version 0.9.5 released ! ##
Exciting new features include the ability to import powerpoint presentations and a new fullscreen mode. A few bugs from the previous versions have been fixed too.
<a href='http://www.youtube.com/watch?feature=player_embedded&v=A68rZl3wt6U' target='_blank'><img src='http://img.youtube.com/vi/A68rZl3wt6U/0.jpg' width='425' height=344 /></a>

## 24 December 2008. Version 0.9.2 ##
Now users can set preferences for various aspects of how eepee functions.

## 15 October 2008. Version 0.9.1 ##
Apart from a few bug fixes, the major change is the ability to create, edit and load playlists. Try it out and as always, suggestions and comments are welcome.

## 01 October 2008. Version 0.9.0 released. Try it out ! ##
This is the next generation eepee. Many new features make it much more comfortable to use compared to the previous versions. The important changes are -
  1. No need for an image editor to preprocess most images. Images can be cropped and rotated in eepee. This does not modify the original image, but the crop and rotate parameters are reapplied the next time the image is opened.
  1. Multiple calipers can now be active on the image. Caliper management is much easier and intuitive now.
  1. Measurement is now displayed over the image along with the calipers.
  1. Images can be saved in different formats.

A [video on Youtube](http://www.youtube.com/watch?v=REZXxo_uDGA) serves as sparse documentation for now !

## 09 August 2008. Version 0.8.0 released ##
After a fairly long break, a new version is released. A fair amount of code has been rewritten under the hood. A lot of design decisions had to be taken and some experimental features introduced in previous version have been rolled back.
**There is a change in the way notes and calibration are stored so that data stored with the previous versions will not be accessible from this version.**

You can download the screencast (in flash format) for a quick introduction to the features.

Latest screenshot

![http://lh4.ggpht.com/rajajs/SJ5tLo77ZSI/AAAAAAAAA_0/618qLKVjJgI/s400/eepee_crushed.png](http://lh4.ggpht.com/rajajs/SJ5tLo77ZSI/AAAAAAAAA_0/618qLKVjJgI/s400/eepee_crushed.png)


## 27 December, 2007. Version 0.7.0 released ##

Many small bug fixes. One particularly nasty bug that has been fixed was the inability to open tiff files with the windows binary (Thanks Imad, for alerting me !). Another small improvement is that the program wont litter with '.note' files everytime you open an image, unless you write notes or calibrate the image.

A new feature that has been added is the ability to add slides to each image. More details on this is available in HowToUse. This feature is still a little flaky, but I hope it to have it more refined by the next version.

Also available to download is a set of sample images to test drive the new features.

## 04 November,2007. Version 0.6.0 released ##

Significant changes include a better status bar and stored calibration values for each image. Windows installer is now available.

## Screenshot (version 0.5.0) ##

![http://lh4.google.com/rajajs/RyNq3mEiLdI/AAAAAAAAAvI/_WqxsKl3XQg/Screenshotsm.png](http://lh4.google.com/rajajs/RyNq3mEiLdI/AAAAAAAAAvI/_WqxsKl3XQg/Screenshotsm.png)