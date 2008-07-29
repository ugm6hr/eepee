set PIP=c:\Python25\pyinstaller-1.3\
python %PIP%Makespec.py --onefile --noconsole --icon=icon32.ico epviewer0.6.0.py
python %PIP%Build.py epviewer0.6.0.spec