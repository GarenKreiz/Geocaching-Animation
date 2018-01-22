#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Generation of an animation film showing the development of geocaches in France
# Generation d'une animation montrant le développement des géocaches en France
#
# Copyright GarenKreiz at  geocaching.com or on  YouTube 
# Auteur    GarenKreiz sur geocaching.com ou sur YouTube
#
# Example:
#   http://www.youtube.com/watch?v=dQEG5hvDyGs
#
# Requires:
#   Python environment (tested with version 2.6.5, 2.7.10)
#   GPXParser module from http://pinguin.uni-psych.gwdg.de/~ihrke/wiki/index.php/GPXParser.py
#   PIL the Python Imaging Library to generate the images of the animation
#   mencoder from MPlayer package to generate the video from images
#   GPX file or CSV export file containing the caches' information (see loadFromCSV method)
#
# Command line parameters:
#   use --help command
#
# Examples:
#   generateAnimation.py -f Cote_Bretagne.gpx -f Cote_Atlantique.gpx -f Cote_Manche.gpx\
#     -l Geocaching_all_logs_Garenkreiz.htm -g "Garenkreiz"  -c white -p -z _Bretagne_ -x GC_Bretagne_errors.txt GC_Bretagne.csv
#
# Additionnal parameters in the code:
#   - zones      : definition of the zone to display (region, country, ...)
#   - logos      : to decorate the images
#   - texts      : to add some texts like music attribution or copyright
#   - showCaches : to emphasize special caches (colored circle)
#   - bigPixels  : to choose the size of the dots for caches
#   - noText     : don't display any text
#   - lastDay    : last day of the animation period
#   - miscellanous sizes for text, images, etc...
#   
# Notes:
#   Many thanks to VNC (www.geocaching-france.com) and eolas (www.mides.fr) for the data on France
#   If you use this program, I'd appreciate to hear from you!
#
# Licence:
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import sys
import time
import math
import string
import getopt
import GPXParser

import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

####################################################################
# data structures for customizing the images and videos
#

# default zone to display (can be changed with the -z argument)
# begins with _ if not a real country used in the geocache description
currentZone = 'France'

# bounding rectangle of the zone (country or state)

zones = {
  '_World_':  (u"Evolution du géocaching dans les territoires français",
               90.00,      # north
               -90.00,     # south
               -180.0  ,   # west
               180.0,      # east 
               (3.5,4.4),  # scale : adapt to fit to video size and preserve X/Y ratio
               (10,-10)),    # offset for x,y coordinates
  '_World1_':  ("Evolution of geocaching",
               55.08917,   # north
               30.33333,   # south
               -120.150,   # west
               20.5600,    # east
               (0.15,0.3), # scale : adapt to fit to video size and preserve X/Y ratio
               (200,10)),  # offset for x,y coordinates

  'Finland':  ("Evolution of geocaching in Finland",
               71.0,
               59.0,
               19.0,
               32.0,
               (25,55),
               (200,30)),
  'France' :  (u"16 ans de géocaching en France métropolitaine",
               51.08917,   # dunes du Perroquet, Bray-Dunes près de Zuydcoote
               41.33333,   # cap di u Beccu, Iles Lavezzi, Corse
               -5.15083,   # phare de Nividic, Ouessant
               9.56000,    # plage Fiorentine, Alistro, Corse
               (48,64),
               (200,80)),
  '_Bretagne_' : (u"Evolution du géocaching en Bretagne",
               48.92,      # Roches Douvres?
               47.24,      # Pointe sud de Belle Ile?
               -5.17,      # Phare de Nividic?
               -0.8,       # Sud du péage de la Gravelle?
               (246,325),
               (20,50)),
  '_Centre_' : (u"Evolution du géocaching en région Centre",
               49,      # Roches Douvres?
               46,      # Pointe sud de Belle Ile?
               -1,      # Phare de Nividic?
               4,       # Sud du péage de la Gravelle?
               (150,210),
               (40,30)),
  '_Loir-et-Cher_' : (u"Evolution du géocaching en Loir-et-Cher",
               48.2,      # Roches Douvres?
               47.18,      # Pointe sud de Belle Ile?
               0.5,      # Phare de Nividic?
               2.4,       # Sud du péage de la Gravelle?
               (435,609),
               (70,-20)),
  '_Europe_': ("Geocaching evolution in Europe",
               70.0,
               27.0,
               -30.0,
               40.0,
               (10 ,20),
               (200,10)),
  }

# texts for write on each frame of the animation (attribution for example)
#    (text, position x, position y)

texts = [
  #(u"génération: Garenkreiz", 35, 95),
  (u"génération: Garenkreiz (CC BY-NC-SA)", 35, 625),
  #(u"licence: CC BY-NC-SA", 35, 655),
  #(u"musique: Winter Is Coming (Andrey Avkhimovich)", 35, 650),
  #(u"musique: Pedro Collares (Gothic)", 35,80),
  #(u"musique: ProleteR (April Showers)", 35,80),
  #(u"musique: Söd'Araygua (Somni Cristallitzat)", 35,80),
  ]

# additionnal pictures to draw on each frame of the animation
#    (image file, position x, position y, size x, size y

logos = [
  #('Logo_1.png',1035,20, 224, 224),
  #('Logo_2.png',1035,480, 224, 224),
  #('Logo_3.png',1053,272, 224,224),
  #('Logo_Loir-et-Cher.jpg',1035,20, 224, 224),
  #'Logo_Breizh_Geocacheurs.png',1035,480, 224, 224),
  #('Logo_Geocaching_16_years.png',1035,272, 224,224),
  #'Logo_Geocaching_15_years.png',1053,272, 224,224),
  #('Plaque_15_ans_white.png',30,440, 240, 200),
  #'Plaque_15_ans_black.png',30,440, 240, 200),
  ]

# emphasize some caches
showCaches = [
  #("GC6GFKY",10,"green"),
  #("GC39D0",4,"yellow"),
  ]

bigPixels = 1           # draw big pixels : 0, 1, 2 ,3
noText = False          # drawing text and logos

# last day of displayed period
# can be set to another specific date 
 
lastDay = time.time() # today
# lastDay = int(time.mktime(time.strptime("2016-08-02", "%Y-%m-%d")))
# lastDay = int(time.mktime(time.strptime("2018-02-03", "%Y-%m-%d")))

# size of output image : 720p or 1080p (HD)
videoRes = 720
if videoRes == 720:
  xSize,ySize=1280,720     # 720p
else:
  xSize,ySize=1120,1080    # HD 1080p

imagesDir = 'Images/'    # directory of generated images

# color types of items (caches, lines,...) 
ARCHIVED    = 0
ACTIVE      = 1
UNAVAILABLE = 2
EVENT       = 3
TRACK       = 4  # visit to cache location by the chosen geocacher
FRONTIER    = 5  # drawing natural or articial topographic features
PLACED      = 6  # cache placed by geocacher
POLYGON     = 7  # polygon to select a drawing area

# searching for a string pattern in a previously opened file

def fileFindNext(f,pattern):

  l = f.readline()
  while l <> '' and not re.search(pattern,l, re.IGNORECASE):
    l = f.readline()
  return l

# compute distance between two points on Earth surface

def getDistance(lat1, lng1, lat2, lng2):

  #
  # calculate the distance (air) in km between 2 points given their coordinates
  #
  # circumference at equator in km
  circ = 24830.0 * 1.609344

  lat1,lng1 = math.radians(lat1),math.radians(lng1)
  lat2,lng2 = math.radians(lat2),math.radians(lng2)
  
  a = lng1 - lng2
  if a < 0.0:
    a = -a
  if a > math.pi:
      a = 2.0 * math.pi - a
  angle = math.acos(math.sin(lat2) * math.sin(lat1) +\
                    math.cos(lat2) * math.cos(lat1) * math.cos(a))
  
  distance = circ * angle / (2.0 * math.pi)
  return distance

def isInsideZone(x, y, points):
    """
    Return True if a coordinate (x, y) is inside a polygon defined by
    a list of verticies [(x1, y1), (x2, x2), ... , (xN, yN)].

    Reference: http://www.ariel.com.au/a/python-point-int-poly.html
    """
    n = len(points)-1
    inside = False
    p1x, p1y = points[0].xy()
    for i in range(1, n + 1):
        p2x, p2y = points[i % n].xy()
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside
include = True
class GCAnimation:

  def __init__(self,currentZone,printing=False, backgroundColor="black", excludedCaches=[]):

    # getting zone parameters
    (title, maxLat, minLat, minLon, maxLon, scaleXY, offsetXY) = zones[currentZone]
    # positionning topographic items within image
    (xOrigin,yOrigin) = offsetXY
    (scaleX,scaleY) = scaleXY
    self.minLon, self.maxLon = minLon, maxLon
    self.minLat, self.maxLat = minLat, maxLat
    self.xOrigin, self.yOrigin = xOrigin, yOrigin
    self.title = title
    
    self.frontiers = []
    self.polygons = []
    self.geocacher = None
    self.printing = printing
    self.color = backgroundColor
    self.excludedCaches = excludedCaches
    self.guids = {}

    print "Background color:",self.color
    if self.color == "white":
      self.background, self.foreground = "white","black"
      self.foreground = "black"
    else:
      self.background, self.foreground = "black", "white"
      #logos.append(('Logo_bas_gauche_black.png',30,440, 240, 200))

    if os.name <> 'posix' or sys.platform == 'cygwin' or sys.platform == "linux2":
      # Windows fonts
      # fontPath = "c:\Windows\Fonts\ARIAL.TTF"
      fontPath = "arial.ttf"
      fontPathFixed = "cour.ttf"
    else:
      # Linux fonts
      fontPath = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
      fontPathFixed = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"

    try:
      if videoRes == 720:
        self.fontArial = ImageFont.truetype ( fontPath, 48 )
      else:
        self.fontArial = ImageFont.truetype ( fontPath, 40 ) # 1080p
      self.fontArialSmall = ImageFont.truetype ( fontPath, 16 )
      self.fontFixed = ImageFont.truetype ( fontPathFixed, 32 )
    except:
      print "Problem initializing fonts"
      sys.exit()

    print "Size :", xSize, ySize
    print "Scale origine:", scaleX, scaleY
    self.scaleX,  self.scaleY  = scaleX, scaleY
    self.XMinLon, self.XMaxLon = (minLon - 0.05), (maxLon + 0.15)
    self.YMinLat, self.YMaxLat = (minLat - 0.1), (maxLat + 0.1)

    self.LX = int((self.XMaxLon-self.XMinLon)*self.scaleX)
    self.LY = int((self.YMaxLat-self.YMinLat)*self.scaleY)
    
    print 'Dimensions:', self.LX, self.LY

    if (self.LX > xSize) or (self.LY > ySize):
      print "Scale too large"
      self.LX,self.LY = xSize,ySize
    print 'Final dimensions:', self.LX, self.LY
    self.LX,self.LY = xSize,ySize
    print 'Original dimensions:', self.LX, self.LY

    self.allWpts = {}       # list of all GC waypoints
    self.coords = {}        # coordinates of GC waypoints
    self.wptStatus = {}     # status of GC waypoints (active, archived, ...)
    self.tracks = []        # list of visit tracks to display
    self.tracksCoords = []  # last coordinate on track displayed
    self.tracksName = []    # name of geocacher or name of TB
    
    # animation of the creation or disparition of a cache : list of pixels to lighten up for each of the 16 animation frames
    # the position is relative to the location of the cache
    # 0 : cache archiving, 1: cache activation
    self.flashAnimation = { 
      0: { # circles getting smaller
        0:  [(-8,+8),(+8,+8),(-8,-8),(+8,-8),(-9,+9),(+9,+9),(-9,-9),(+9,-9),(-11,0),(+11,0),(0,-11),(0,+11)],
        1:  [(-8,+8),(+8,+8),(-8,-8),(+8,-8),(-10,0),(+10,0),(0,-10),(0,+10)],
        2:  [(-7,+7),(+7,+7),(-7,-7),(+7,-7),(-8,+8),(+8,+8),(-8,-8),(+8,-8),(-10,0),(+10,0),(0,-10),(0,+10)],
        3:  [(-7,+7),(+7,+7),(-7,-7),(+7,-7),(-9,0),(+9,0),(0,-9),(0,+9)],
        4:  [(-6,+6),(+6,+6),(-6,-6),(+6,-6),(-7,+7),(+7,+7),(-7,-7),(+7,-7),(-9,0),(+9,0),(0,-9),(0,+9)],
        5:  [(-6,+6),(+6,+6),(-6,-6),(+6,-6),(-8,0),(+8,0),(0,-8),(0,+8)],
        6:  [(-5,+5),(+5,+5),(-5,-5),(+5,-5),(-6,+6),(+6,+6),(-6,-6),(+6,-6),(-8,0),(+8,0),(0,-8),(0,+8)],
        7:  [(-5,+5),(+5,+5),(-5,-5),(+5,-5),(-7,0),(+7,0),(0,-7),(0,+7)],
        8:  [(-4,+4),(+4,+4),(-4,-4),(+4,-4),(-5,+5),(+5,+5),(-5,-5),(+5,-5),(-7,0),(+7,0),(0,-7),(0,+7)],
        9:  [(-4,+4),(+4,+4),(-4,-4),(+4,-4),(-5,0),(+5,0),(0,-5),(0,+5)],
        10: [(-3,+3),(+3,+3),(-3,-3),(+3,-3),(-4,+4),(+4,+4),(-4,-4),(+4,-4),(-5,0),(+5,0),(0,-5),(0,+5)],
        11: [(-3,+3),(+3,+3),(-3,-3),(+3,-3),(-4,0),(+4,0),(0,-4),(0,+4)],
        12: [(-2,+2),(+2,+2),(-2,-2),(+2,-2),(-3,+3),(+3,+3),(-3,-3),(+3,-3),(-4,0),(+4,0),(0,-4),(0,+4)],
        13: [(-2,+2),(+2,+2),(-2,-2),(+2,-2),(-3,0),(+3,0),(0,-3),(0,+3)],
        14: [(-1,+1),(+1,+1),(-1,-1),(+1,-1),(-2,+2),(+2,+2),(-2,-2),(+2,-2),(-3,0),(+3,0),(0,-3),(0,+3)],
        15: [(-1,+1),(+1,+1),(-1,-1),(+1,-1)],
        16: [(-1,+1),(+1,+1),(-1,-1),(+1,-1)],
        },
      1: { # blinking star
        0: [(-1,0),(+1,0),(0,-1),(0,+1)],
        1: [(-2,0),(-1,0),(+1,0),(+2,0),(0,-2),(0,-1),(0,+1),(0,+2)],
        2: [(-2,0),(-1,0),(+1,0),(+2,0),(0,-2),(0,-1),(0,+1),(0,+2),(-3,0),(+3,0),(0,-3),(0,+3)],
        3: [(-2,0),(-1,0),(+1,0),(+2,0),(0,-2),(0,-1),(0,+1),(0,+2),(-3,0),(+3,0),(0,-3),(0,+3),(-5,0),(+5,0),(0,-5),(0,+5)],
        4: [(-2,0),(-1,0),(+1,0),(+2,0),(0,-2),(0,-1),(0,+1),(0,+2),(-3,0),(+3,0),(0,-3),(0,+3)],
        5: [(-2,0),(-1,0),(+1,0),(+2,0),(0,-2),(0,-1),(0,+1),(0,+2)],
        6: [(-1,0),(+1,0),(0,-1),(0,+1)],
        7: [],
        8: [],
        9: [],
        10: [],
        11: [],
        12: [],
        13: [],
        14: [],
        15: [],
        16: [],
        },
      }
    
    # 0,255,0 : green - 0,255,255 : light blue - 255,0,0 : red
    # 255,255,0 : yellow - 255,0,255 : purple - 0,0,255 : blue
    self.flashColor = {
        ARCHIVED    : (255,0,255), # purple for archiving
        ACTIVE      : (255,255,0), # yellow for creation
        PLACED      : (255,255,0), # yellow for creation
        }
    if self.color == "white":
      self.cacheColor = {
        ARCHIVED    : (178,34,34),   # firebrick
        ACTIVE      : (0,0,128),     # navy
        UNAVAILABLE : (255,102,0),   # orange
        EVENT       : (0,255,0),     # green
        TRACK       : (255,0,255),   # purple
        FRONTIER    : (0,0,255),     # blue
        PLACED      : (255,255,0),   # yellow
        }
    else:
      self.cacheColor = {
        ARCHIVED    : (255,0,0),   # red
        ACTIVE      : (0,255,255), # light blue
        UNAVAILABLE : (255,102,0), # orange
        EVENT       : (0,255,0),   # green
        TRACK       : (255,0,255), # purple
        FRONTIER    : (0,0,255),   # blue
        PLACED      : (255,255,0), # yellow
        }
      
    self.flashCursor = 0
    self.flashLength = len(self.flashAnimation[0])
    self.flashList = {}
    for active in range(0,2):
      self.flashList[active] = {}
      for i in range(0,self.flashLength):
        self.flashList[active][i] = []


  def drawPoint(self,status,x,y):

    self.imResult.putpixel((x,y),self.cacheColor[status])
    shape = []
    if bigPixels > 0:
      shape += [(1,0),(0,1),(1,1)]
    if bigPixels > 1 or status == PLACED:
      shape += [(-1,0),(0,-1),(-1,-1),(-1,1),(1,-1)]
    if bigPixels > 2 or status == PLACED:
      shape += [(-2,0),(0,-2),(2,0),(0,2),(-2,-2),(-2,2),(2,-2),(2,2)]
      shape += [(-2,1),(1,-2),(2,1),(1,2)]
      shape += [(-2,-1),(-1,-2),(2,-1),(-1,2)]
    for (dx,dy) in shape:
      self.imResult.putpixel((x+dx,y+dy),self.cacheColor[status]) 


  def newItem(self,name,lat,lon,status,eventTime):

    if eventTime == None:
      print "Problem with time of cache ",name
      sys.exit()
    self.coords[name] = (lat,lon)
    try:
      if not (lat,lon,name,status) in self.allWpts[eventTime]:
        self.allWpts[eventTime].insert(0,(lat,lon,name,status))
        self.nAddedCaches += 1
    except:
      self.allWpts[eventTime] = [(lat,lon,name,status)]
      self.nAddedCaches += 1
    return


  def convertDate(self,dateString):

    if dateString <> "":
      strTime = dateString+" 00:00:01Z"
      for pattern in ["%d/%m/%Y %H:%M:%SZ", "%Y/%m/%d %H:%M:%SZ", "%d %b %y %H:%M:%SZ"]:
        try:
          t = int(time.mktime(time.strptime(strTime, pattern)))
          return t
        except:
          pass
    return 0


  def loadFromFile(self,file,geocacher=None,status=ACTIVE):

    if geocacher:
      if re.search("\|",geocacher):
        self.geocacher = re.sub("\(([^|]+)\|.*\)","\\1",geocacher)
      else:
        self.geocacher = geocacher
      logoGeocacher = 'Avatar_'+self.geocacher+'.png'
      if os.path.isfile(logoGeocacher):
        logos.append((logoGeocacher,1035,20, 224, 224))
      
    if file[-4:].lower() == '.gpx':
      self.loadFromGPX(file,status=status)
    else:
      self.loadFromCSV(file,geocacher)


  def loadLogsFromFile(self,myFile):

    print 'Processing logs file:', myFile
    if myFile[-5:].lower() == '.html' or myFile[-4:].lower() == '.htm':
      self.loadLogsFromHTML(myFile)
    else:
      self.loadLogsFromCSV(myFile)

      
  def loadLogsFromCSV(self,myCSV):
  
    logs = {}
    fInput = open(myCSV,'r')
    l = fInput.readline()
    while l <> '':
      try:
        (cacheName, dateFound) = string.split(l.strip(),"|")
        dateLog = self.convertDate(dateFound)
        try:
          # reverse order for each day
          logs[dateLog].insert(0,cacheName)
        except:
          logs[dateLog] = [cacheName]
        print dateFound, logs[dateLog]
      except Exception, msg:
        print "Pb logs:",msg
      l = fInput.readline()

    print '  Logs loaded:',len(logs)
    
    self.tracks.append(logs)
    self.tracksCoords.append((0.0,0.0))
    self.tracksName = "";
      
  def loadLogsFromHTML(self,myHTML):

    print 'Processing tracks file:', myHTML
    logs = {}
    
    fInput = open(myHTML,'r')
    searching = 0
    nbLogs = 0

    # parsing HTML to find earch log entry
    l = fileFindNext(fInput,"All Logs")
    while l <> '':
      l = fileFindNext(fInput,"<tr")
      l = fileFindNext(fInput,"<img")
      type = re.sub('.*alt="','',l.strip())
      type = re.sub('".*','',type)
      nbLogs += 1
      l = fileFindNext(fInput,"<td>")
      l = fileFindNext(fInput,"<td>")
      if re.search('</TD',l,re.IGNORECASE):
        dateString = re.sub('.*<(TD|td)> *','',l)
        dateString = re.sub(' .*','',dateString)
        dateString = dateString.strip()
      else:
        dateString = fInput.readline().strip()
      cacheTime = self.convertDate(dateString)
      print dateString,
      l = fileFindNext(fInput,"<a")
      guid = re.sub('.*guid=','',l.strip())
      guid = re.sub('".*','',guid)
      print guid,

      # keeping visits to cache location
      if type in ['Found it','Didn\'t find it','Attended','Owner Maintenance']:
        try:
          (name, lat,lon) = self.guids[guid]
          self.newItem(name,lat,lon,TRACK,cacheTime)
          
          #try:
          #  # reverse order for each day
          #  logs[cacheTime].insert(0,(float(lat),float(lon)))
          #except:
          #  logs[cacheTime] = [(float(lat),float(lon))]
          print ":", name, lat, lon, type
        except:
          print ": unknown cache or outside zone"
      else:
        print " --- ", type

    print '  Logs loaded:',nbLogs
    
    #self.tracks.append(logs)
    #self.tracksCoords.append((0.0,0.0))
    #self.tracksName.append(self.geocacher)
    return

      
  def loadFromCSV(self,myCSV,geocacher=None):

    # Fields included in the GSAK view used to export to CSV
    #   Code,Cache Type,Note,Last4Logs,Last Log,Waypoint Name,Placed By,Placed,Last Found,Found,Country,Lat,Lon,Status,Url,Found by me,Owner Id

    print 'Processing CSV file:', myCSV
    
    fInput = open(myCSV,'r')
    if geocacher <> None:
      geocacher = geocacher.upper()
    self.nAddedCaches = 0
    l = fInput.readline()
    while l <> '':
      fields = re.sub('[\n\r]*','',l)
      fields = re.sub('\|','&#108;',fields)      # cache names containing character |
      fields = re.sub('","','|',fields[1:-1])    # getting rid of all double quotes used by GSAK
      fields = string.split(fields,"|")
      try:
        (name,cacheType,note,last4logs,dateLastLog,wpName,placedBy,datePlaced,dateLastFound,found,country,latitude,longitude,status,url,dateFoundByMe,ownerId) = fields[0:17]
      except Exception, msg:
        print msg, fields
        break 
      
      if name == "Code GC" or name == "Code" or name in self.excludedCaches:
        # first line of headers in export file of GSAK
        # tested for French and English
        l = fInput.readline()
        continue
      elif currentZone[0] <> '_' and country <> currentZone:
        print '!!! Pb cache outside',currentZone,':',name
        l = fInput.readline()
        continue

      lat, lon = float(latitude), float(longitude)

      if include and self.polygons <> []:
        # find if cache is inside one of the polygons
        inside = False
        p = 0 
        while not inside and p < len(self.polygons):
          (latMin, latMax, lonMin, lonMax) = self.polygons[p].bbox()
          if lat >= latMin and lat <= latMax and lon >= lonMin and lon <= lonMax:
            inside = isInsideZone(lat, lon, self.polygons[p].wpts)  
          p += 1
        if not inside:
          #print'!!! Outside of zone polygon', name, latitude, longitude
          #print "= NOK =",l
          l = fInput.readline()
          continue

      print "= OK =",l,

      guid = re.sub('.*guid=','',url)
      self.guids[guid] = (name,latitude,longitude)
      if cacheType == "Event Cache" or cacheType == "Cache In Trash Out Event":
        status = EVENT                     # Event cache
      elif status == 'X':
        status = ARCHIVED                  # Archived
      elif status == 'T':
        status = UNAVAILABLE               # Temporarily unavailable
      else:
        status = ACTIVE                    # Active cache 

      lat,lon = float(latitude),float(longitude)
      if (lat > self.maxLat) or (lat < self.minLat) or \
         (lon > self.maxLon) or (lon < self.minLon) or (currentZone[0] <> '_' and country <> currentZone and country <> ''):
        print '!!! Pb point outside the drawing zone:',name, lat, ' not in ', self.minLat, self.maxLat, self.minLon, self.maxLon
        l = fInput.readline()
        continue

      cacheTime = self.convertDate(datePlaced)
      lastFoundTime = self.convertDate(dateLastFound)
      lastLogTime = self.convertDate(dateLastLog)
      foundByMeTime = self.convertDate(dateFoundByMe)

      if status <> EVENT:
        # a non-event cache is active for a while after being placed
        # uncertainty between placed date and publication date
        # cache placed by geocacher : only work if no change in pseudos
        if geocacher <> None and re.search(geocacher,placedBy.upper()):
          self.newItem(name,lat,lon,PLACED,cacheTime)
          # cache placed by geocacher : only work if no change in pseudos
          print "Placed: "+name
        else:
          self.newItem(name,lat,lon,ACTIVE,cacheTime)
        if status <> ACTIVE:
          # the cache isn't active anymore
          if lastLogTime == 0:
            # 20 days : dummy date for archiving time 
            lastLogTime = cacheTime + 20*24*3600
          self.newItem(name,lat,lon,status,lastLogTime)
      else:
        if geocacher <> None and re.search(geocacher,placedBy.upper()):
          self.newItem(name,lat,lon,PLACED,cacheTime)
          # cache placed by geocacher : only work if no change in pseudos
          print "Placed: "+name
        else:
          self.newItem(name,lat,lon,status,cacheTime)
          
      l = fInput.readline()
    fInput.close()
        
    print 'Added caches:',self.nAddedCaches

  def loadFromGPX(self,file,status=ACTIVE):

    print 'Processing GPX file:',file

    myGPX = GPXParser.GPXParser(file)
    print '  Waypoints found :',len(myGPX.wpts)
    print '  Tracks found :',len(myGPX.trcks)
    
    if status == FRONTIER or status == POLYGON:
      for t in myGPX.trcks:
        for s in t.segs:
            self.frontiers.append(s)
            if status == POLYGON:
              self.polygons.append(s)
      return
    
    self.foundWpts = {}
    self.nAddedCaches = 0
      
    for p in myGPX.wpts:
      name =  p.attribs['name']
      if (name[0:2] <> 'GC'):
          continue
      lat,lon = p.lat,p.lon

      try:
        country = p.attribs['groundspeak:country']
      except:
        country = ''

      if (lat > self.maxLat) or (lat < self.minLat) or \
         (lon > self.maxLon) or (lon < self.minLon):
        print '!!! Pb point outside the drawing area :', p.attribs['name'], lat, lon, ' not in ', self.minLat, self.maxLat, self.minLon, self.maxLon
        continue

      strTime = p.attribs['time']
      strTime = re.sub('\..*','',strTime)
      strTime = re.sub('Z$','',strTime)
      cacheTime = int(time.mktime(time.strptime(strTime, "%Y-%m-%dT%H:%M:%S")))

      if p.attribs['type'] == 'Geocache|Event Cache' or p.attribs['type'] == 'Geocache|Cache In Trash Out Event':
        cacheStatus = EVENT
      else:
        cacheStatus = status
      if cacheStatus == ACTIVE:
        try:
          result = self.foundWpts[name]
          # cache already listed as inactive, don't activate it
        except:
          self.foundWpts[name] = cacheStatus
      else:
          self.foundWpts[name] = cacheStatus
      self.newItem(name,lat,lon,cacheStatus,cacheTime)
    print 'Added caches',self.nAddedCaches
    print 'Caches :',len(self.foundWpts)


  def generateText(self,img,cacheTime):
    
    self.imTempDraw = ImageDraw.Draw(img)
    text = time.strftime("%d/%m/%Y : ",time.localtime(cacheTime))
    text += "%5d cache"%self.nCaches
    if self.nCaches > 1:
      text += "s"
    if currentZone == '_Bretagne_':
      text += " bretonne"
      if self.nCaches > 1:
        text += "s"
    if self.geocacher:
      self.imTempDraw.text((40,self.LY-83), text, font=self.fontFixed, fill=self.foreground)
      text = self.geocacher + " : "+ ("%d"%self.nPlaced)+u" création"
      if self.nPlaced > 1:
        text += "s"
      text += " / %d visite"%self.nVisits
      if self.nVisits > 1:
        text  += "s"
      if self.distance > 0: 
        text += " - %.0f kms"%self.distance
      self.imTempDraw.text((40,self.LY-43), text, font=self.fontFixed, fill=self.foreground)
    else:
      self.imTempDraw.text((40,self.LY-43), text, font=self.fontFixed, fill=self.foreground)


  def generateFlash(self,LX,LY,nDays,cacheTime):

    box = self.imResult.crop((0,0,self.LX,self.LY))
    self.imTemp = Image.new('RGB',(self.LX,self.LY),self.background)
    self.imTemp.paste(box,(0,0,self.LX,self.LY))

    for status in range(0,2):
      for i in range(0,self.flashLength):
        for (dx,dy) in self.flashAnimation[status][(i-self.flashCursor)%self.flashLength]:
          for (x,y) in self.flashList[status][i]:
            try:
              self.imTemp.putpixel((x+dx,y+dy),self.flashColor[status]) # yellow flash: cache activation, purple one for archiving
            except:
              print '!!! Pb writing pixel', x+dx, y+dy, nDays, time.asctime(time.localtime(cacheTime))

    # next step of the animation of the flash
    self.flashCursor = (self.flashCursor - 1) % self.flashLength
    for status in range(0,2):
      self.flashList[status][self.flashCursor] = []
      
    self.generateText(self.imTemp,cacheTime)
    
    self.imTemp.save(imagesDir+'map%04d.png'%nDays,"PNG")
    sys.stdout.write('.')
    sys.stdout.flush()

  def latlon2xy(self,lat,lon):
    
    x = self.xOrigin + int(self.scaleX*(lon-self.XMinLon))
    y = self.yOrigin + int(self.scaleY*(self.YMaxLat-lat))
    return (x,y)


  def drawTracks(self, cachingTime):

    draw = ImageDraw.Draw(self.imResult)
    for i in range(len(self.tracks)):
      t = self.tracks[i]
      try:
        caches = t[cachingTime]
        (latOld,lonOld) = self.tracksCoords[i]
        (xOld, yOld) = self.latlon2xy(latOld,lonOld)
        for c in caches:
          if c[0:2] == 'GC':
            (lat,lon) = self.coords[c]
          else:
            (lat,lon) = c
          (x,y) = self.latlon2xy(lat,lon)
          if (latOld,lonOld) <> (0.0,0.0):
            draw.line([(xOld, yOld),(x,y)], self.cacheColor[TRACK])
            if self.geocacher and self.geocacher == self.tracksName[i]:
              self.distance += getDistance(latOld,lonOld,lat,lon)
          latOld,lonOld = lat,lon
          xOld,yOld = x,y
          self.tracksCoords[i] = (lat,lon)
      except Exception, msg:
        print msg
        pass


  def generatePreview(self, geocacher=None):

    # generate a preview of all caches
    tempImg = self.imResult
    box = self.imResult.crop((0,0,self.LX,self.LY))
    imTemp = Image.new('RGB',(self.LX,self.LY),self.background)
    imTemp.paste(box,(0,0,self.LX,self.LY))
    self.imResult = imTemp

    times = self.allWpts.keys()
    times.sort()
    for cacheTime in times:
      for (lat,lon,name,status) in self.allWpts[cacheTime]:
        # x = int(self.scaleX*(lon-self.XMinLon)) # 720p
        (x,y) = self.latlon2xy(lat,lon)
        if not geocacher or status == PLACED:
          self.drawPoint(status,x,y)
    if geocacher:
      fileName = 'Geocaching_'+currentZone+'_'+geocacher
    else:
      fileName = 'Geocaching_'+currentZone
    print "Preview image : "+imagesDir+fileName+'.png'
    self.imResult.save(imagesDir+fileName+'.png',"PNG")
    if geocacher:
      self.drawTracks(time.time())
      print "Preview image : "+imagesDir+fileName+'_tracks.png'
      self.imResult.save(imagesDir+fileName+'_tracks.png',"PNG")
    self.imResult = tempImg


  def generateImages(self, tracing):

    print "Generating images"

    try:
      os.mkdir(imagesDir)
      print 'Created directory ' + imagesDir
    except:
      print 'Images in directory ' + imagesDir


    self.imResult = Image.new('RGB',(self.LX,self.LY),self.background)

    imDraw = ImageDraw.Draw(self.imResult)

    print "Drawing frontiers"
    
    for f in self.frontiers:
      xOld, yOld = 0, 0
      for p in f.wpts:
        (x,y) = self.latlon2xy(p.lat,p.lon)
        if (xOld, yOld) <> (0,0):
          imDraw.line([(xOld, yOld),(x,y)], self.cacheColor[FRONTIER])
        xOld, yOld = x, y
      
    self.imResult.save(imagesDir+'Geocaching_'+currentZone+'_frontieres.png',"PNG")

    if not noText:
      for (logoImage,logoX,logoY, sizeX, sizeY) in logos:
        logo = Image.open(logoImage)
        logo = logo.convert("RGBA")
        if logo.size[0] > sizeX or logo.size[1] > sizeY:
          logo = logo.resize((sizeX,sizeY), PIL.Image.ANTIALIAS)
        self.imResult.paste(logo,(logoX,logoY),logo)

    if not noText:
      imDraw.text((30,15),   self.title                      , font=self.fontArial     , fill="red")
      if self.color == "white":
        textColor = "black"
      else:
        textColor = "red"
      for (t,x,y) in texts:
        imDraw.text((x,y), t, font=self.fontArialSmall, fill=textColor)

    # misc counters
    nDays = 0
    self.nCaches = 0
    nActive = 0
    nUnavailable = 0
    nArchived = 0
    self.nVisits = 0            # visits of a geocacher : found, did not found
    self.nPlaced = 0            # cache placed or event organized
    

    # variables to display the geocacher's moves
    latOld,lonOld = 0.0,0.0 
    xOld,yOld = 0,0
    self.distance = 0

    maxArchived, minArchived = 0, 0
    maxUnavailable, minUnavailable = 0, 0
    maxActive, minActive = 0, 0
    
    nbStatuses = { ACTIVE: 0, UNAVAILABLE: 0, ARCHIVED: 0, EVENT:0, TRACK:0, PLACED: 0}
    nbStatusesPrevious = dict(nbStatuses)

    self.generatePreview()
    if geocacher:
      self.generatePreview(self.geocacher+"_")

    cacheTimes = self.allWpts.keys()
    cacheTimes.sort()

    if len(cacheTimes) == 0:
      return

    # generate the first image without any cache
    self.generateFlash(self.LX,self.LY,nDays,cacheTimes[0])

    # initialize the time of the current frame to the first date
    previousTime = cacheTimes[0]

    for cacheTime in cacheTimes:
      # don't display future dates corresponding to future events
      if cacheTime > lastDay:
          cacheTime = lastDay
          break

      dArchived = 0
      dUnavailable = 0
      dActive = 0

      # print time.asctime(time.localtime(cacheTime))
      # generate intermediate images for each days between last cache day and current day
      for cachingTime in range(previousTime+24*3600, cacheTime, 24*3600):
          nDays= nDays + 1
          self.drawTracks(cachingTime)
          if not printing:
            self.generateFlash(self.LX,self.LY,nDays,cachingTime)

      self.drawTracks(cacheTime)

      self.draw = ImageDraw.Draw(self.imResult)

      nDays = nDays + 1

      for (lat,lon,name,status) in self.allWpts[cacheTime]:
        # x = int(self.scaleX*(lon-self.XMinLon)) # 720p
        (x,y) = self.latlon2xy(lat,lon)
        # print 'Cache placed:',time.asctime(time.localtime(cacheTime)), name, (lat,lon) , (x,y)

        try:
            if self.wptStatus[name] <> status:
              nbStatuses[self.wptStatus[name]] -= 1
              nbStatuses[status] += 1
              self.wptStatus[name] = status
        except:
          self.wptStatus[name] = status
          nbStatuses[status] += 1
        
        if status == UNAVAILABLE:
          nUnavailable += 1
          self.flashList[1][self.flashCursor].append((x,y))
        elif status == ACTIVE or status == PLACED:
          nActive += 1
          self.flashList[1][self.flashCursor].append((x,y))
        elif status == ARCHIVED:
          nArchived += 1
          self.flashList[0][self.flashCursor].append((x,y))

        if status == ACTIVE or status == PLACED or status == EVENT:          # active caches or events
          self.nCaches += 1
          if status == PLACED:
            self.nPlaced += 1
        try:
          if status == TRACK or status == PLACED:                            # drawing moves of a geocacher
            if (latOld,lonOld) <> (0.0,0.0):
              self.draw.line([(xOld, yOld),(x,y)], self.cacheColor[TRACK])
              self.distance += getDistance(latOld,lonOld,lat,lon)
            self.nVisits += 1
            # del draw
            xOld,yOld = x,y
            latOld,lonOld = lat,lon
          self.drawPoint(status,x,y)
        except Exception, msg:
          print '!!! Pb point outside the drawing area:',lat, lon, name, x, y, status, msg

      if nbStatuses <> nbStatusesPrevious:
        dArchived    = nbStatuses[0] - nbStatusesPrevious[0]
        dUnavailable = nbStatuses[1] - nbStatusesPrevious[1]
        dActive      = nbStatuses[2] - nbStatusesPrevious[2]
        nbStatusesPrevious = dict(nbStatuses)
      
      maxArchived = max(maxArchived,dArchived)
      maxUnavailable = max(maxUnavailable,dUnavailable)
      maxActive = max(maxActive,dActive)
      minArchived = min(minArchived,dArchived)
      minUnavailable = min(minUnavailable,dUnavailable)
      minActive = min(minActive,dActive)
      
      if not printing:
        self.generateFlash(self.LX,self.LY,nDays,cacheTime)

      previousTime = cacheTime

    # display the final situation during a few seconds
    if not printing:
      for i in range(nDays,nDays+100):
    	self.generateFlash(self.LX,self.LY,i,cacheTime)

    if self.printing:
      cacheTime = lastDay
    self.generateText(self.imResult,cacheTime)
    draw = ImageDraw.Draw(self.imResult)
    for (cache,size,color) in showCaches:
      print "Showing special cache:",cache
      try:
        (lat,lon) = self.coords[cache]
        (x, y) = self.latlon2xy(lat,lon)
        draw.ellipse((x-size,y-size,x+size,y+size), fill=color)
      except:
        pass
    
    # final view of all caches
    self.imResult.save(imagesDir+'Geocaching_'+currentZone+'.png',"PNG")

    print "Global view:",imagesDir+'Geocaching_'+currentZone+'.png'
    
    if self.geocacher:
      self.generatePreview(self.geocacher)

    print ''
    print 'Processed ', self.nCaches, 'caches'
    print 'Processed ', nActive, 'active caches'
    print 'Processed ', nUnavailable, 'unavailable caches'
    print 'Processed ', nArchived, 'archived caches'

    if not printing:
      fOut = open(imagesDir+'listPNG.txt','w')
      for i in range(0,50):
        # fill some images at the beginning
        fOut.write('map0000.png\n')
      for i in range(0,nDays+1):
        fOut.write('map%04d.png\n'%i)
      for i in range(nDays+1,nDays+100):
        # some still frames to finish the video
        fOut.write('map%04d.png\n'%nDays)
      fOut.close()
    
if __name__=='__main__':
  
  def usage():
    print 'Usage: python generationAnimation.py <active_caches.gpx>'
    print 'Usage: python generationAnimation.py <gsak_extract.csv> [ <name of geocacher> ]'
    print '-g <geocacher name> : display activity of the geocacher'
    print '-f <frontier gpx file> : display the frontiers or coastlines'
    print '-l <logged caches file> : process "all logs" HTML file'
    print '-z <zone> : restrict display to zone'
    print '-x <file of cache ids> : exclude the caches from the animation'
    print '-p : printing'
    print '-c <color>: background color (white or black)'
    print '-a <archived_caches.gpx>: list of cache that are now archived'
    print '<caches file> : CSV table of caches'
    print ''
    print 'Note : some arguments can be used multiple times (-f, -l, etc...)'
    print 'Note : some parameters are set in the source code (title, music, logo, etc...)'
    
    sys.exit(2)
    
  geocacher = None
  color = False
  printing = False
  archived = []
  frontiers = []
  polygons = []
  tracks = []
  logs = []
  excludeCaches = None
  excludedCaches = []
  
  print sys.argv[1:]
  
  try:
    opts, args = getopt.getopt(sys.argv[1:],"hpa:c:f:g:i:l:x:z:")
  except getopt.GetoptError:
    usage()

  if opts == []:
    usage()
    
  for opt, arg in opts:
    if opt == '-h':
      # help
      usage()
    elif opt == "-p":
      # generate a image for printing (no animation)
      printing = True
    elif opt == "-c":
      # choos the main background color (black ou white)
      color = arg
    elif opt == "-a":
      # load a file of archived caches
      archived.append(arg)
    elif opt in ("-g", "--geocacher"):
      # name of the geocacher
      geocacher = arg
    elif opt in ("-f", "--frontiers"):
      # load GPX file to display a frontier or coast
      frontiers.append(arg)
    elif opt in ("-i", "--inside"):
      # display only geocaches inside the given GPX polygon
      polygons.append(arg)
    elif opt in ("-z", "--zone"):
      # use the template to display the named zone (scale and offset)
      currentZone = arg
    elif opt in ("-x", "--exclude"):
      # exclude a list of caches (when the region is wrong)
      excludeCaches = arg
    elif opt in ("-l", "--logs"):
      # load a file containing the logs of a cacher to display the moves
      logs.append(arg)
      
  print archived
  print frontiers
  
  myAnimation = GCAnimation(currentZone,printing,color,excludedCaches)

  if excludeCaches and os.path.isfile(excludeCaches):
    with open(excludeCaches,'r') as f:
      for x in f.readlines():
        excludedCaches.append(x.strip())
  print excludedCaches

  for file in frontiers:
    myAnimation.loadFromGPX(file,status=FRONTIER)

  for file in polygons:
    myAnimation.loadFromGPX(file,status=POLYGON)

  for file in args:
    print "Loading file:", file
    myAnimation.loadFromFile(file,geocacher)

  for file in archived:
    print "Loading archived file", file
    myAnimation.loadFromFile(file,geocacher,status=ARCHIVED)
    
  for file in logs:
    myAnimation.loadLogsFromFile(file)

  #try:
  myAnimation.generateImages(tracing=True)
  #except Exception, msg:
  #  print "Problem in generation:", msg
    
  print 'That\'s all folks!'
  print 'Next step : mencoder "mf://map*.png" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'
  print 'Next step : mencoder "mf://@listPNG.txt" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'

