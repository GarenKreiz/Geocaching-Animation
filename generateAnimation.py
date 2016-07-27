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
# Requires:
#   Python environment (tested with version 2.6.5, 2.7.10)
#   GPXParser module from http://pinguin.uni-psych.gwdg.de/~ihrke/wiki/index.php/GPXParser.py
#   PIL the Python Imaging Library to generate the images of the animation
#   mencoder from MPlayer package to generate the video from images
#   GPX file or CSV export file containing the caches' information (see loadFromCSV method)

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

# zone to display (can be changed with the -z argument)
# begins with _ if not a real country used in the geocache description
currentZone = '_Bretagne_'

# bounding rectangle of the country or state

zones = {
  '_World_':  (55.08917,   # north
               30.33333,   # south
               -120.150,   # west
               20.5600,    # east 
               (0.15,0.3), # scale : adapt to fit to video size and preserve X/Y ratio
               (200,10)),  # offset for x,y coordinates
  'France' :  (51.08917,   # dunes du Perroquet, Bray-Dunes près de Zuydcoote
               41.33333,   # cap di u Beccu, Iles Lavezzi, Corse
               -5.15083,   # phare de Nividic, Ouessant
               9.56000,    # plage Fiorentine, Alistro, Corse
               (50,70),
               (200,10)),
  '_Bretagne_' :
              (48.92, 
               47.24, 
               -5.17, 
               -0.8,  
               #(180,250),
               #(200,280),
               #(242,320),
               (246,325),
               (20,50)),
  '_Europe_': (80.0,
               27.0,
               -30.0,
               40.0,
               (10 ,20),
               (200,10)),
  }

# additionnal pictures to draw on each frame of the animation
logoImages = [
  ('Breizh_Geocacheurs_blanc.png',1035,490),
  ('Geocaching_15_years.png',1050,272),
  #('Garenkreiz_cercle_noir.png',1035,20)
  #('Avatar_c2ic.png',1035,20)
  ]

(maxLatCountry, minLatCountry, minLonCountry, maxLonCountry, scaleXY, offsetXY) = zones[currentZone]

# size of output image : 720p or 1080p (HD)
videoRes = 720
if videoRes == 720:
  xSize,ySize=1280,720     # 720p
else:
  xSize,ySize=1120,1080    # HD 1080p

# positionning topographic items within image
(xOrigin,yOrigin) = offsetXY

bigPixels = 2           # draw big pixels (2x2), otherwise (1x1)

imagesDir = 'Images/'    # directory of generated images

# color types of items (caches, lines,...) 
ARCHIVED    = 0
ACTIVE      = 1
UNAVAILABLE = 2
EVENT       = 3
TRACK       = 4  # visit to cache location by the chosen geocacher
FRONTIER    = 5  # drawing natural or articial topographic features
PLACED      = 6  # cache placed by geocacher

# searching for a string pattern in a previously opened file
def fileFindNext(f,pattern):
  l = f.readline()
  while l <> '' and not re.search(pattern,l):
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

class GCAnimation:

  def __init__(self,(scaleX,scaleY),minLon,maxLon,minLat,maxLat,printing=False):

    self.minLon, self.maxLon = minLon, maxLon
    self.minLat, self.maxLat = minLat, maxLat
    self.frontiers = []
    self.xOrigin = xOrigin
    self.yOrigin = yOrigin
    self.guids = {}
    self.geocacher = None
    self.printing = printing
    if printing:
      self.background = "white"
      self.foreground = "black"
    else:
      self.background = "black"
      self.foreground = "white"

    print "os.name=",os.name,"sys.platform=",sys.platform
    
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
    self.scaleX,self.scaleY = scaleX,scaleY
    self.XMinLon,self.XMaxLon = (minLon - 0.05),(maxLon + 0.15)
    self.YMinLat,self.YMaxLat = (minLat - 0.1),(maxLat + 0.1)

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
    
    # animation of the creation or disparition of a cache : list of pixels to lighten up for each animation frame
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
    if printing:
      self.cacheColor = {
        ARCHIVED    : (178,34,34),   # firebrick
        ACTIVE      : (0,0,128),     # navy
        UNAVAILABLE : (255,102,0),   # orange
        EVENT       : (0,255,0),     # green
        TRACK       : (255,0,255),   # purple
        FRONTIER    : (0,0,255),     # blue
        PLACED      : (255,255,0),     # darkgreen
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
    if status == PLACED:
      shape += [(-2,0),(0,-2),(2,0),(0,2),(-2,-2),(-2,2),(2,-2),(2,2)]
    for (dx,dy) in shape:
      self.imResult.putpixel((x+dx,y+dy),self.cacheColor[status]) 

  def newItem(self,name,lat,lon,active,eventTime):
    try:
      self.coords[name] = (lat,lon)
      if not (lat,lon,name,active) in self.allWpts[eventTime]:
        self.allWpts[eventTime].append((lat,lon,name,active))
        self.nAddedCaches += 1
    except:
      self.allWpts[eventTime] = [(lat,lon,name,active)]
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
      print "Problem in date format:",dateString
      return 0

  def loadFromFile(self,file,geocacher=None):
    
    if geocacher:
      if re.search("\|",geocacher):
        self.geocacher = re.sub("\(([^|]+)\|.*\)","\\1",geocacher)
      else:
        self.geocacher = geocacher
      logoGeocacher = 'Avatar_'+self.geocacher+'.png'
      if os.path.isfile(logoGeocacher):
        logoImages.append((logoGeocacher,1035,20))
        
    if file[-4:].lower() == '.gpx':
      self.loadFromGPX(file,status=ACTIVE)
    else:
      self.loadFromCSV(file,geocacher)

  def loadLogsFromCSV(self,myCSV):

    print 'Processing logs file:', myCSV
    if myCSV[-5:].lower() == '.html' or myCSV[-4:].lower() == '.htm':
      self.loadLogsFromHTML(myCSV)
      return
  
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
    self.tracksCoords.append((0,0))
      
  def loadLogsFromHTML(self,myHTML):

    print 'Processing tracks file:', myHTML
    logs = {}
    
    fInput = open(myHTML,'r')
    searching = 0
    nbLogs = 0

    # parsing HTML to find earch log entry
    l = fileFindNext(fInput,"All Logs")
    while l <> '':
      l = fileFindNext(fInput,"<tr class")
      l = fileFindNext(fInput,"<img src")
      type = re.sub('.*alt="','',l.strip())
      type = re.sub('".*','',type)
      print "Type :", type,
      nbLogs += 1
      l = fileFindNext(fInput,"<td>")
      l = fileFindNext(fInput,"<td>")
      dateString = fInput.readline().strip()
      dateLog = self.convertDate(dateString)
      print "Date:",dateString,dateLog,
      l = fileFindNext(fInput,"<a href")
      guid = re.sub('.*guid=','',l.strip())
      guid = re.sub('".*','',guid)
      print "Cache",guid,
      logTypes =['Found it','Didn\'t find it','Attended','Owner Maintenance']
      if type in logTypes:
        print ' =============== ',
        try:
          (name, lat,lon) = self.guids[guid]
          try:
            # reverse order for each day
            logs[dateLog].insert(0,(float(lat),float(lon)))
          except:
            logs[dateLog] = [(float(lat),float(lon))]
          print ":", name, lat, lon
        except:
          print ": not present"

    print '  Logs loaded:',nbLogs
    
    self.tracks.append(logs)
    self.tracksCoords.append((0,0))
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
        (name,cacheType,note,last4logs,dateLastLog,wpName,placedBy,datePlaced,dateLastFound,found,country,latitude,longitude,status,url,dateFoundByMe,ownerId) = fields
      except Exception, msg:
        print msg, fields
        break
      if name == "Code GC" or name == "Code":
        # first line of headers in export file of GSAK
        # tested for French and English
        l = fInput.readline()
        continue
      elif currentZone[0] <> '_' and country <> currentZone:
        print '!!! Pb cache outside',currentZone,':',name
        l = fInput.readline()
        continue
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
        print '!!! Pb point outside the drawing zone:',name
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
        else:
          self.newItem(name,lat,lon,ACTIVE,cacheTime)
        if status <> ACTIVE and status <> PLACED:
          # the cache isn't active anymore
          if lastLogTime == 0:
            # dummy date for archiving time
            lastLogTime = cacheTime + 24*3600
          self.newItem(name,lat,lon,status,lastLogTime)
      else:
        self.newItem(name,lat,lon,status,cacheTime)
      if geocacher <> None:
        # cache found by geocacher : if geocacher generated the cache list
        if 1 == 0 and foundByMeTime <> 0:
          print "Found : "+name
          self.newItem(name,lat,lon,TRACK,foundByMeTime)
        # cache placed by geocacher : only work if no change in pseudos
        if re.search(geocacher,placedBy.upper()):
          print "Placed: "+name
          self.newItem(name,lat,lon,TRACK,cacheTime)
      l = fInput.readline()
    fInput.close()
        
    print 'Added caches:',self.nAddedCaches

  def loadFromGPX(self,file,status=ACTIVE):

    print 'Processing GPX file:',file

    myGPX = GPXParser.GPXParser(file)
    print '  Waypoints found :',len(myGPX.wpts)
    print '  Tracks found :',len(myGPX.trcks)
    
    if status == FRONTIER:
      for t in myGPX.trcks:
        self.frontiers.append(t)
      return
    
    self.foundWpts = {}
    self.nAddedCaches = 0
      
    for p in myGPX.wpts:
      lat,lon = p.lat,p.lon

      try:
        country = p.attribs['groundspeak:country']
      except:
        country = ''

      if (lat > self.maxLat) or (lat < self.minLat) or \
         (lon > self.maxLon) or (lon < self.minLon) or (country <> 'France' and country <> ''):
        print '!!! Pb point outside the drawing area :', p.attribs['name'], lat, lon
        continue

      name =  p.attribs['name']
      strTime = p.attribs['time']
      cacheTime = int(time.mktime(time.strptime(strTime, "%Y-%m-%dT%H:%M:%SZ")))
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


  def generateText(self,img,cacheTime,nCaches,geocacher,distance,nVisits):
    self.imTempDraw = ImageDraw.Draw(img)
    text = time.strftime("%d/%m/%Y : ",time.localtime(cacheTime))
    text += "%5d caches"%nCaches
    if currentZone == '_Bretagne_':
      text += " bretonnes"
    if geocacher:
      self.imTempDraw.text((40,self.LY-83), text, font=self.fontFixed, fill=self.foreground)
      text = geocacher + " : %04d visites "%nVisits
      if distance > 0: 
        text += " - %.0f kms"%distance
        self.imTempDraw.text((40,self.LY-43), text, font=self.fontFixed, fill=self.foreground)
    else:
      self.imTempDraw.text((40,self.LY-43), text, font=self.fontFixed, fill=self.foreground)

  def generateFlash(self,myImage,LX,LY,nDays,cacheTime,nCaches,nVisits,distance):
    
    box = myImage.crop((0,0,self.LX,self.LY))
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

    # next step on the animation of the flash
    self.flashCursor = (self.flashCursor - 1) % self.flashLength
    for status in range(0,2):
      self.flashList[status][self.flashCursor] = []
      
    self.generateText(self.imTemp,cacheTime,nCaches,geocacher,distance,nVisits)
    
    self.imTemp.save(imagesDir+'map%04d.png'%nDays,"PNG")
    sys.stdout.write('.')
    sys.stdout.flush()

  def latlon2xy(self,lat,lon):
    x = self.xOrigin + int(self.scaleX*(lon-self.XMinLon)) # 720p
    y = self.yOrigin + int(self.scaleY*(self.YMaxLat-lat))
    return (x,y)

  def drawTracks(self, cachingTime):

    draw = ImageDraw.Draw(self.imResult)
    for i in range(0, len(self.tracks)):
      t = self.tracks[i]
      try:
        caches = t[cachingTime]
        (oldX,oldY) = self.tracksCoords[i]
        for c in caches:
          if c[0:2] == 'GC':
            (lat,lon) = self.coords[c]
          else:
            (lat,lon) = c
          (x,y) = self.latlon2xy(lat,lon)
          if (oldX,oldY) <> (0,0):
            draw.line([(oldX, oldY),(x,y)], self.cacheColor[TRACK])
          oldX,oldY = x,y
          self.tracksCoords[i] = (x,y)
      except Exception, msg:
        pass

  def generatePreview(self, geocacher=None):
    # generate a preview of all caches
    tempImg = self.imResult
    box = self.imResult.crop((0,0,self.LX,self.LY))
    imTemp = Image.new('RGB',(self.LX,self.LY),self.background)
    imTemp.paste(box,(0,0,self.LX,self.LY))
    self.imResult = imTemp
    for cacheTime in self.allWpts.keys():
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
      
    today = time.time()+3600*24*6

    self.imResult = Image.new('RGB',(self.LX,self.LY),self.background)

    imDraw = ImageDraw.Draw(self.imResult)

    for f in self.frontiers:
      xOld, yOld = 0, 0
      for p in f.wpts:
        (x,y) = self.latlon2xy(p.lat,p.lon)
        if (xOld, yOld) <> (0,0):
          imDraw.line([(xOld, yOld),(x,y)], self.cacheColor[FRONTIER])
        xOld, yOld = x, y
      
    self.imResult.save(imagesDir+'Geocaching_'+currentZone+'_frontieres.png',"PNG")


    for (logoImage,logoX,logoY) in logoImages:
      logo = Image.open(logoImage)
      #logo.load()
      #print logoImage, logo.mode
      logo = logo.convert("RGBA")
      if logo.size[0] > 224:
        logo = logo.resize((224,224), PIL.Image.ANTIALIAS)
      #print logoImage, logo.mode
      self.imResult.paste(logo,(logoX,logoY),logo)

    #imDraw.text((30,5),  u"Géocaches en France"                      , font=self.fontArial     , fill="red")
    imDraw.text((30,15),   u"15 ans de géocaching en Bretagne"                      , font=self.fontArial     , fill="green")
    imDraw.text((35,85),  u"génération: GarenKreiz"                     , font=self.fontArialSmall, fill="red")
    #imDraw.text((35,60),  u"musique: Adragante (Variations 3)"         , font=self.fontArialSmall, fill="red")
    imDraw.text((36,110), u"licence: CC BY-NC-SA"                      , font=self.fontArialSmall, fill="red")

    #imDraw.text((35,80),  u"musique: Pedro Collares (Gothic)", font=self.fontArialSmall, fill="red")
    #imDraw.text((35,80),  u"musique: ProleteR (April Showers)", font=self.fontArialSmall, fill="red")
    #imDraw.text((35,80),  u"musique: Söd'Araygua (Somni Cristallitzat)", font=self.fontArialSmall, fill="red")

    # misc counters
    nDays = 0
    nCaches = 0
    nActive = 0
    nUnavailable = 0
    nArchived = 0
    nVisits = 0            # visits of a geocacher : found, did not found
    
    cacheTimes = self.allWpts.keys()
    cacheTimes.sort()

    if len(cacheTimes) == 0:
      return
    # initialize the time of the current frame to the first date
    previousTime = cacheTimes[0]

    # variables to display the geocacher's moves
    latOld,lonOld = 0.0,0.0 
    xOld,yOld = 0,0
    distance = 0

    maxArchived, minArchived = 0, 0
    maxUnavailable, minUnavailable = 0, 0
    maxActive, minActive = 0, 0
    
    nbStatuses = { ACTIVE: 0, UNAVAILABLE: 0, ARCHIVED: 0, EVENT:0, TRACK:0, PLACED: 0}
    nbStatusesPrevious = dict(nbStatuses)

    self.generatePreview()
    if geocacher:
      self.generatePreview(self.geocacher+"_")

    for cacheTime in cacheTimes:
      # don't display future dates corresponding to future events
      if cacheTime > today:
          cacheTime = today
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
            self.generateFlash(self.imResult,self.LX,self.LY,nDays,cachingTime,nCaches,nVisits,distance)

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
          nCaches = nCaches + 1
        try:
          if status == TRACK:                            # drawing moves of a geocacher
            if (xOld,yOld) <> (0,0):
              self.draw.line([(xOld, yOld),(x,y)], self.cacheColor[TRACK])
              distance += getDistance(latOld,lonOld,lat,lon)
              nVisits += 1
            # del draw
            xOld,yOld = x,y
            latOld,lonOld = lat,lon
          else:
            self.drawPoint(status,x,y)
        except Exception, msg:
          print '!!! Pb point outside the drawing area:',lat, lon, name, x, y, status, msg

      # print nbStatuses, nbStatusesPrevious, '===', 
      
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
        self.generateFlash(self.imResult,self.LX,self.LY,nDays,cacheTime,nCaches,nVisits,distance)

      previousTime = cacheTime

    print 'Max:', maxArchived, maxUnavailable, maxActive
    print 'Min:', minArchived, minUnavailable, minActive
    # display the final situation during a few seconds
    if not printing:
      for i in range(nDays,nDays+100):
    	self.generateFlash(self.imResult,self.LX,self.LY,i,cacheTime,nCaches,nVisits,distance)

    self.generateText(self.imResult,cacheTime,nCaches,self.geocacher,distance,nVisits)
    
    # final view of all caches
    self.imResult.save(imagesDir+'Geocaching_'+currentZone+'.jpg')
    self.imResult.save(imagesDir+'Geocaching_'+currentZone+'.png',"PNG")
    if geocacher:
      self.generatePreview(self.geocacher)

    print ''
    print 'Processed ', nCaches, 'caches'
    print 'Processed ', nActive, 'active caches'
    print 'Processed ', nUnavailable, 'unavailable caches'
    print 'Processed ', nArchived, 'archived caches'


    if not printing:
      fOut = open(imagesDir+'listPNG.txt','w')
      # fill some images at the end, synchronising with music 
      for i in range(0,nDays+1):
        fOut.write('map%04d.png\n'%i)
      for i in range(nDays+1,max(nDays+100,5400)):
        fOut.write('map%04d.png\n'%nDays)
      fOut.close()
    
if __name__=='__main__':
  

  def usage():
    print 'Usage: python generationAnimation.py <active_caches.gpx> [ ... <archived_caches.gpx> ]'
    print 'Usage: python generationAnimation.py <gsak_extract.csv> [ <name of geocacher> ]'
    print '-g <geocacher name> : display activity of the geocacher'
    print '-f <frontier gpx file> : display the frontiers or coastlines'
    print '-l <logged caches file> : process "all logs" HTML file'
    print '-z <zone> : restrict display to zone'
    print '-p : white background for printing'
    print '<caches file> : CSV table of caches'
    print ''
    print 'Note : some arguments can be used multiple times (-f, -l, etc...)'
    print 'Note : some parameters are set in the source code (title, music, logo, etc...)'
    
    sys.exit(2)
    
  geocacher = None
  printing = False
  archived = []
  frontiers = []
  tracks = []
  logs = []
  excludeCaches = ''
  
  print sys.argv[1:]
  
  try:
    opts, args = getopt.getopt(sys.argv[1:],"hpg:f:l:x:z:")
  except getopt.GetoptError:
    usage()

  if opts == []:
    usage()
    
  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt == "-p":
      printing = True
    elif opt in ("-g", "--geocacher"):
      geocacher = arg
    elif opt in ("-f", "--frontiers"):
      frontiers.append(arg)
    elif opt in ("-z", "--zone"):
      currentZone = arg
    elif opt in ("-x", "--exclude"):
      excludeCaches = arg
    elif opt in ("-l", "--logs"):
      logs.append(arg)
  print archived
  print frontiers
  
  myAnimation = GCAnimation(scaleXY,minLonCountry,maxLonCountry,minLatCountry,maxLatCountry,printing)

  for file in args:
    print "Loading file:", file
    myAnimation.loadFromFile(file,geocacher)

  for file in frontiers:
    myAnimation.loadFromGPX(file,status=FRONTIER)

  for file in logs:
    myAnimation.loadLogsFromCSV(file)

  try:
    myAnimation.generateImages(tracing=True)
  except Exception, msg:
    print "Pb:",msg

  print 'That\'s all folks!'
  print 'Next step : mencoder "mf://map*.png" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'
  print 'Next step : mencoder "mf://@listPNG.txt" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'

