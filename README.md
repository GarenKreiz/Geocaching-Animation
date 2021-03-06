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

Some reuses of the code or the idea

- [2009/06 France](https://www.youtube.com/watch?v=0Gae6M3l4xE)
- [2009/06 New Zealand](https://www.youtube.com/watch?v=1JLkAZ0vFp4&t=28s)
- [2009/06 New Australia](https://www.youtube.com/user/caughtatwork/videos)
- [2009/06 Switzerland](http://www.youtube.com/watch?v=NPoFT96Ve50 )
- [2009/07 Germany](https://www.youtube.com/watch?v=pOiHPPlSxi4 )
- [2010/10 Portugal](http://www.youtube.com/watch?v=MddsTfFeSIQ )
- [2010/11 Sweden](http://www.youtube.com/watch?v=Y2JaJ5ki9lc )
- [2010/11 Denmark](http://www.youtube.com/watch?v=ZEz2f2F5PKo )
- [2011/05 Czech Republic](https://www.youtube.com/watch?v=JW-FP1ebcL0)
- [2011/07 Australia](http://www.youtube.com/watch?v=wXrVHSm3oGg )
- [2011/09 Canada](http://www.youtube.com/watch?v=a1bvCO5-zpY )  
- [2009/06 New Zealand](https://www.youtube.com/watch?v=1JLkAZ0vFp4&t=28s)
- [2015/06 United Kingdom](https://www.youtube.com/watch?v=ayhYVRVE9Ac)
- [2016/10 Europe](https://www.youtube.com/watch?v=DkU56zSPgR0)
- [2017/03 Finland](https://www.youtube.com/watch?v=0cKnomvwFPs)

Notes
* The version of the GPX parser used can't ingest large GPX files (30000 geocaches). 
* The CSV file can be generated by any program (GSAK, script, spreadsheet, ...) but the program is currently tuned to accept export files from GSAK (the list of the columns can be customized using the "View" menu of GSAK). 


 
