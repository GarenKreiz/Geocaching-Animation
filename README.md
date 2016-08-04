Geocaching Animation
by GarenKreiz

Python program to generate images for animation videos showing the creation and evolution of geocaches in a given area. It can also display the visits of a geocacher (currently Found caches)

It was used to display the evolution of geocaching in France http://www.youtube.com/watch?v=dQEG5hvDyGs

Requirements
- Python environment (tested with version 2.6.5 and 2.7.10)
- GPXParser module from http://pinguin.uni-psych.gwdg.de/~ihrke/wiki/index.php/GPXParser.py
- PIL or PILLOW, the Python Imaging Library to generate the images of the animation
- mencoder from MPlayer package to generate the video from images

Inputs
- GPX file or CSV export file containing the caches' information (see loadFromCSV method)
- GPX files used for drawing the coastline or frontiers of the choosen area

Notes
* The version of the GPX parser used can't ingest large GPX files (30000 geocaches). 
* The CSV file can be generated by any program (GSAK, script, spreadsheet, ...) but the program is currently tuned to accept export files from GSAK (the list of the columns can be customized using the "View" menu of GSAK). 


 