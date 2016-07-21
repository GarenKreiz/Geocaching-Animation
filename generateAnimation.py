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

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# zone to display (the last one is used, to change simply change the order)
# begin with _ if not a real country used in the geocache description
currentZone = '_World_'
currentZone = '_Europe_'
currentZone = '_Bretagne_'
currentZone = 'France'

# additionnal picture to draw on each frame of the animation
logoImage = 'logo_breizh_geocacheurs.jpg' 
logoX = 1040
logoY = 505

# bounding rectangle of the country or state

zones = {
  'France' :  (51.08917,  # dunes du Perroquet, Bray-Dunes près de Zuydcoote
               41.33333,  # cap di u Beccu, Iles Lavezzi, Corse
               -5.15083,  # phare de Nividic, Ouessant
               9.56000,   # plage Fiorentine, Alistro, Corse
               #(75,107)),
               (50,70)),
  '_Bretagne_' :
              (48.92, 
               47.24, 
               -5.17, 
               -0.8,  
               (180,250)),
  '_World_':  (55.08917,  # north
               30.33333,  # south
               -120.150,  # west
               20.5600,   # east 
               (0.15,0.3)),# adapt to fit to video size and preserve X/Y ratio
  '_Europe_': (80.0,
               27.0,
               -30.0,
               40.0,
               (10 ,20)),
  }

(maxLatCountry, minLatCountry, minLonCountry, maxLonCountry, scaleXY) = zones[currentZone]

# size of output image : 720p or 1080p (HD)
videoRes = 720
if videoRes == 720:
  xSize,ySize=1280,720     # 720p
else:
  xSize,ySize=1120,1080    # HD 1080p

xOrigin,yOrigin=200,0

bigPixels = 1            # draw big pixels (2x2), otherwise (1x1)

imagesDir = 'Images/'    # directory of generated images

# color types of items (caches, lines,...) 
ARCHIVED    = 0
ACTIVE      = 1
UNAVAILABLE = 2
EVENT       = 3
TRACK       = 4
BLACK       = 5
FRONTIER    = 6

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

  def __init__(self,(scaleX,scaleY),minLon,maxLon,minLat,maxLat):

    self.minLon, self.maxLon = minLon, maxLon
    self.minLat, self.maxLat = minLat, maxLat
    self.frontiers = []
    self.xOrigin = xOrigin
    self.yOrigin = yOrigin
    
    if os.name <> 'posix' or sys.platform == 'cygwin':
      # Windows fonts
      # fontPath = "c:\Windows\Fonts\ARIAL.TTF"
      fontPath = "arial.ttf"
      fontPathFixed = "cour.ttf"
    else:
      # Linux fonts
      fontPath = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
      fontPathFixed = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"

    if videoRes == 720:
      self.fontArial = ImageFont.truetype ( fontPath, 32 )
    else:
      self.fontArial = ImageFont.truetype ( fontPath, 40 ) # 1080p
    self.fontArialSmall = ImageFont.truetype ( fontPath, 16 )
    self.fontFixed = ImageFont.truetype ( fontPathFixed, 32 ) 

    print "Size :", xSize, ySize
    print "Scale origine:", scaleX, scaleY
    self.scaleX,self.scaleY = scaleX,scaleY
    self.XMinLon,self.XMaxLon = (minLon - 0.05),(maxLon + 0.15)
    self.YMinLat,self.YMaxLat = (minLat - 0.1),(maxLat + 0.1)

    print "X MinMax:", self.XMinLon,self.XMaxLon
    print "Y MinMax:", self.YMinLat,self.YMaxLat
    #self.scaleY = ySize/(self.YMaxLat-self.YMinLat)
    #self.scaleX = xSize/(self.XMaxLon-self.XMinLon)
    print "Scale computed :",self.scaleX, self.scaleY
    #self.scaleX = self.scaleY*scaleX/scaleY
    print "Scale finale:", self.scaleX, self.scaleY

    self.LX = int((self.XMaxLon-self.XMinLon)*self.scaleX)
    self.LY = int((self.YMaxLat-self.YMinLat)*self.scaleY)
    
    print 'Dimensions:', self.LX, self.LY
    if (self.LX > xSize) or (self.LY > ySize):
      print "Scale too large"
      self.LX,self.LY = xSize,ySize
    # self.LX,self.LY = xSize,ySize
    print 'Final dimensions:', self.LX, self.LY
    self.LX,self.LY = xSize,ySize
    print 'Original dimensions:', self.LX, self.LY

    self.allWpts = {}     # list of all GC waypoints
    self.coords = {}      # coordinates of GC waypoints
    self.wptStatus = {}
    self.tracks = []      # visit tracks to display
    self.tracksCoords = []    # last coordinate of visit displayed on track
    
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
      }
    self.cacheColor = {
      ARCHIVED    : (255,0,0),   # red
      ACTIVE      : (0,255,255), # light blue
      UNAVAILABLE : (255,102,0), # orange
      EVENT       : (0,255,0),   # green
      TRACK       : (255,0,255), # purple
      BLACK       : (0,0,0),     # black
      FRONTIER    : (0,0,255),   # blue
      }
      
    self.flashCursor = 0
    self.flashLength = len(self.flashAnimation[0])
    self.flashList = {}
    for active in range(0,2):
      self.flashList[active] = {}
      for i in range(0,self.flashLength):
        self.flashList[active][i] = []

  def drawPoint(self,active,x,y):

    self.imResult.putpixel((x,y),self.cacheColor[active])
    if bigPixels == 1:
      self.imResult.putpixel((x+1,y),self.cacheColor[active]) 
      self.imResult.putpixel((x,y+1),self.cacheColor[active]) 
      self.imResult.putpixel((x+1,y+1),self.cacheColor[active])
  
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
      try:
        t = int(time.mktime(time.strptime(strTime, "%d/%m/%Y %H:%M:%SZ")))
      except:
        try:
          t = int(time.mktime(time.strptime(strTime, "%Y/%m/%d %H:%M:%SZ")))
        except:
          print "Pb in time 1", strTime
        print "Pb in time 2 [", strTime, "]"
      return t
    else:
      return 0

  def loadFromFile(self,file,geocacher=None):
        
    if file[-4:].lower() == '.gpx':
      self.loadFromGPX(file,status=ACTIVE)
    else:
      self.loadFromCSV(file,geocacher)

  def loadLogsFromCSV(self,myCSV):

    print 'Processing logs file:', myCSV
    logs = {}
    
    fInput = open(myCSV,'r')
    l = fInput.readline()
    while l <> '':
      try:
        (cacheName, dateFound) = string.split(l.strip(),"|")
        foundTime = self.convertDate(dateFound)
        try:
          # reverse order for each day
          logs[foundTime].insert(0,cacheName)
        except:
          logs[foundTime] = [cacheName]
        print dateFound, logs[foundTime]
      except Exception, msg:
        print "Pb logs:",msg
      l = fInput.readline()

    print '  Logs loaded:',len(logs)
    
    self.tracks.append(logs)
    self.tracksCoords.append((0,0))
      
  def loadTracksFromCSV(self,myCSV):

    print 'Processing tracks file:', myCSV
    logs = {}
    
    fInput = open(myCSV,'r')
    l = fInput.readline()
    while l <> '':
      try:
        (dateFound,lat,lon) = string.split(l.strip(),"|")
        foundTime = self.convertDate(dateFound)
        try:
          # reverse order for each day
          logs[foundTime].insert(0,(float(lat),float(lon)))
        except:
          logs[foundTime] = [(float(lat),float(lon))]
        print dateFound, logs[foundTime]
      except Exception, msg:
        print "Pb logs:",msg
      l = fInput.readline()

    print '  Logs loaded:',len(logs)
    
    self.tracks.append(logs)
    self.tracksCoords.append((0,0))
      
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
      (name,cacheType,note,last4logs,dateLastLog,wpName,placedBy,datePlaced,dateLastFound,found,country,latitude,longitude,status,url,dateFoundByMe,ownerId) = fields
      if name == "Code GC" or name == "Code":
        # first line of headers in export file of GSAK
        # tested for French and English
        l = fInput.readline()
        continue
      elif currentZone[0] <> '_' and country <> currentZone:
        print '!!! Pb cache outside',currentZone,':',name
        l = fInput.readline()
        continue

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
        # print '!!! Pb point outside the drawing zone:',name
        l = fInput.readline()
        continue

      cacheTime = self.convertDate(datePlaced)
      lastFoundTime = self.convertDate(dateLastFound)
      lastLogTime = self.convertDate(dateLastLog)
      foundByMeTime = self.convertDate(dateFoundByMe)
      
      if status <> EVENT:
        # a non-event cache is active for a while after being placed
        self.newItem(name,lat,lon,1,cacheTime)
        if status <> ACTIVE:
          # the cache isn't active anymore
          if lastLogTime == 0:
            lastLogTime = cacheTime + 24*3600
          self.newItem(name,lat,lon,status,lastLogTime)
      else:
        self.newItem(name,lat,lon,status,cacheTime)
      if geocacher <> None:
        if foundByMeTime <> 0:
          self.newItem(name,lat,lon,TRACK,foundByMeTime)
        if re.search(geocacher,placedBy.upper()):
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
      print name
      
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


  def generateFlash(self,myImage,LX,LY,nDays,cacheTime,nbCaches, distance):
    
    box = myImage.crop((0,0,self.LX,self.LY))
    self.imTemp = Image.new('RGB',(self.LX,self.LY),0)
    self.imTemp.paste(box,(0,0,self.LX,self.LY))

    for status in range(0,2):
      for i in range(0,self.flashLength):
        for (dx,dy) in self.flashAnimation[status][(i-self.flashCursor)%self.flashLength]:
          for (x,y) in self.flashList[status][i]:
            try:
              self.imTemp.putpixel((x+dx,y+dy),self.flashColor[status]) # yellow flash: cache activation, purple one for archiving
            except:
              print '!!! Pb writing pixel', nDays, x, y, dx, dy, x+dx, y+dy

    # next step on the animation of the flash
    self.flashCursor = (self.flashCursor - 1) % self.flashLength
    for status in range(0,2):
      self.flashList[status][self.flashCursor] = []

    self.imTempDraw = ImageDraw.Draw(self.imTemp)
    text = time.strftime("%d/%m/%Y",time.localtime(cacheTime))+" : %5d caches"%nbCaches
    if distance > 0:
      text = text+" - %.0f kms"%distance
    self.imTempDraw.text((130,self.LY-43), text, font=self.fontFixed, fill="blue")
    self.imTemp.save(imagesDir+'map%04d.png'%nDays,"PNG")
    sys.stdout.write('.')
    sys.stdout.flush()

  def drawStats(self,nDays,nArchived,nUnavailable,nActive,dArchived,dUnavailable,dActive):
    day = nDays % 700

    scaleStats = 800
    offsetStats = 900

    # print 'Stats:',nDays,nArchived,nUnavailable,nActive,dArchived,dUnavailable,dActive
    draw = ImageDraw.Draw(self.imResult)
    draw.rectangle([1000,10,1200,700],outline=self.cacheColor[BLACK],fill=self.cacheColor[BLACK])
    yStart = 700
    draw.rectangle([1000,yStart,1200,yStart-dArchived],outline=self.cacheColor[ARCHIVED],fill=self.cacheColor[ARCHIVED])
    yStart -= dArchived
    draw.rectangle([1000,yStart,1200,yStart-dUnavailable],outline=self.cacheColor[UNAVAILABLE],fill=self.cacheColor[UNAVAILABLE])
    yStart -= dUnavailable
    draw.rectangle([1000,yStart,1200,yStart-dActive],outline=self.cacheColor[ACTIVE],fill=self.cacheColor[ACTIVE])
    
    
    xActive = int(nActive/scaleStats)
    xUnavailable = int(nUnavailable/scaleStats)
    xArchived = int(nArchived/scaleStats)
    draw.line([(offsetStats, day+11),(self.LX,day+11)], self.cacheColor[BLACK])
    draw.line([(offsetStats, day+12),(self.LX,day+12)], self.cacheColor[BLACK])
    draw.line([(offsetStats, day+13),(self.LX,day+13)], self.cacheColor[BLACK])
    draw.line([(offsetStats, day+14),(self.LX,day+14)], self.cacheColor[BLACK])
    xStart = offsetStats
    draw.line([(xStart, day+10),(xStart + xArchived,day+10)], self.cacheColor[ARCHIVED])
    xStart += xArchived + 1
    draw.line([(xStart, day+10),(xStart + xUnavailable,day+10)], self.cacheColor[ACTIVE])
    xStart += xUnavailable + 1
    draw.line([(xStart, day+10),(xStart + xActive,day+10)], self.cacheColor[ACTIVE])

  def latlon2xy(self,lat,lon):
    x = self.xOrigin + int(self.scaleX*(lon-self.XMinLon)) # 720p
    y = self.yOrigin + int(self.scaleY*(self.YMaxLat-lat))
    # print (lat,lon), (self.xOrigin, self.yOrigin), (self.scaleX, self.scaleY), (self.XMinLon, self.YMaxLat), "=>", (x,y)
    return (x,y)

  def drawTracks(self, cachingTime):

    draw = ImageDraw.Draw(self.imResult)
    for i in range(0, len(self.tracks)):
      t = self.tracks[i]
      try:
        caches = t[cachingTime]
        (oldX,oldY) = self.tracksCoords[i]
        print "Visits:",caches, (oldX,oldY),
        for c in caches:
          if c[0:2] == 'GC':
            (lat,lon) = self.coords[c]
          else:
            (lat,lon) = c
          (x,y) = self.latlon2xy(lat,lon)
          print x,y
          if (oldX,oldY) <> (0,0):
            draw.line([(oldX, oldY),(x,y)], self.cacheColor[TRACK])
          print 'Cache visit :',time.asctime(time.localtime(cachingTime)), c, (lat,lon),(oldX,oldY),x,y
          oldX,oldY = x,y
          self.tracksCoords[i] = (x,y)
      except Exception, msg:
        pass
      
  def generateImages(self, tracing):

    print "Generating images"

    try:
      os.mkdir(imagesDir)
      print 'Created directory ' + imagesDir
    except:
      print 'Images in directory ' + imagesDir
      
    today = time.time()

    self.imResult = Image.new('RGB',(self.LX,self.LY),0)

    imDraw = ImageDraw.Draw(self.imResult)

    for f in self.frontiers:
      xOld, yOld = 0, 0
      for p in f.wpts:
        (x,y) = self.latlon2xy(p.lat,p.lon)
        if (xOld, yOld) <> (0,0):
          imDraw.line([(xOld, yOld),(x,y)], self.cacheColor[FRONTIER])
        xOld, yOld = x, y
      
    self.imResult.save(imagesDir+'Geocaching_France_frontieres.png',"PNG")


    logo = Image.open(logoImage)
    self.imResult.paste(logo,(logoX,logoY))
    
    #imDraw.text((30,5),  u"Géocaches en France"                      , font=self.fontArial     , fill="red")
    imDraw.text((30,5),   u"Géocaches en Bretagne"                      , font=self.fontArial     , fill="red")
    imDraw.text((35,50),  u"animation: GarenKreiz"                     , font=self.fontArialSmall, fill="red")
    imDraw.text((35,80),  u"musique: Adragante (Variations 3)"         , font=self.fontArialSmall, fill="red")
    imDraw.text((36,110), u"licence: CC BY-NC-SA"                      , font=self.fontArialSmall, fill="red")

    #imDraw.text((35,80),  u"musique: Pedro Collares (Gothic)", font=self.fontArialSmall, fill="red")
    #imDraw.text((35,80),  u"musique: ProleteR (April Showers)", font=self.fontArialSmall, fill="red")
    #imDraw.text((35,80),  u"musique: Söd'Araygua (Somni Cristallitzat)", font=self.fontArialSmall, fill="red")

    # misc counters
    nDays = 0
    nActive = 0
    nUnavailable = 0
    nArchived = 0
    nCaches = 0
    
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
    
    nbStatuses = { ACTIVE: 0, UNAVAILABLE: 0, ARCHIVED: 0, EVENT:0, TRACK:0}
    nbStatusesPrevious = dict(nbStatuses)
    
    print self.tracks
    
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
          # self.drawStats(nDays,nArchived,nUnavailable,nActive,dArchived,dUnavailable,dActive)
          self.generateFlash(self.imResult,self.LX,self.LY,nDays,cachingTime,nCaches,distance)


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
        elif status == ACTIVE:
          nActive += 1
          self.flashList[1][self.flashCursor].append((x,y))
        elif status == ARCHIVED:
          nArchived += 1
          self.flashList[0][self.flashCursor].append((x,y))


        if status == ACTIVE or status == EVENT:          # active caches or events
          nCaches = nCaches + 1
        try:
          if status == TRACK:                            # drawing moves of a geocacher
            if (xOld,yOld) <> (0,0):
              self.draw.line([(xOld, yOld),(x,y)], self.cacheColor[TRACK])
              distance += getDistance(latOld,lonOld,lat,lon)
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
      
      # self.drawStats(nDays,nArchived,nUnavailable,nActive,dArchived,dUnavailable,dActive)
      self.generateFlash(self.imResult,self.LX,self.LY,nDays,cacheTime,nCaches, distance)

      previousTime = cacheTime

    print 'Max:', maxArchived, maxUnavailable, maxActive
    print 'Min:', minArchived, minUnavailable, minActive
    # display the final situation during a few seconds
    for i in range(nDays,nDays+100):
    	self.generateFlash(self.imResult,self.LX,self.LY,i,cacheTime,nCaches, distance)

    # final view of all caches
    self.imResult.save(imagesDir+'Geocaching_France.jpg')
    self.imResult.save(imagesDir+'Geocaching_France.png',"PNG")
    print ''
    print 'Processed ', nCaches, 'caches'
    print 'Processed ', nActive, 'active caches'
    print 'Processed ', nUnavailable, 'unavailable caches'
    print 'Processed ', nArchived, 'archived caches'

    fOut = open(imagesDir+'listPNG.txt','w')
    # fill some images at the end, synchronising with music 
    for i in range(0,nDays+1):
      fOut.write(imagesDir+'map%04d.png\n'%i)
    for i in range(nDays+1,max(nDays+100,5400)):
      fOut.write(imagesDir+'map%04d.png\n'%nDays)
    fOut.close()
    
if __name__=='__main__':
  

  def usage():
    print 'Usage: python generationAnimation.py <active_caches.gpx> [ ... <archived_caches.gpx> ]'
    print 'Usage: python generationAnimation.py <gsak_extract.csv> [ <name of geocacher> ]'
    print '-g <geocacher name>'
    print '-f <frontier gpx file>'
    print '-a <archived caches file>'
    print '-l <logged caches file>'
    print '<active caches file>'
    print ''
    print 'Note : some arguments can be used multiple times (-f, -a, -l, etc...)'
    print 'Note : some parameters are set in the source code (zone, title, music, logo, etc...)'
    
    sys.exit(2)
    
  geocacher = None
  archived = []
  frontiers = []
  tracks = []
  logs = []
  currentZone = "_World_"
  
  print sys.argv[1:]
  
  try:
    opts, args = getopt.getopt(sys.argv[1:],"ha:g:f:l:t:z:")
  except getopt.GetoptError:
    usage()

  if opts == []:
    usage()
    
  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt in ("-g", "--geocacher"):
      geocacher = arg
    elif opt in ("-a", "--archived"):
      archived.append(arg)
    elif opt in ("-f", "--frontiers"):
      frontiers.append(arg)
    elif opt in ("-z", "--zone"):
      currentZone = arg
    elif opt in ("-t", "--tracks"):
      tracks.append(arg)
    elif opt in ("-l", "--logs"):
      logs.append(arg)
  print archived
  print frontiers
  
  myAnimation = GCAnimation(scaleXY,minLonCountry,maxLonCountry,minLatCountry,maxLatCountry)

  for file in args:
    print "Loading file:", file
    myAnimation.loadFromFile(file,geocacher)

  for file in archived:
    myAnimation.loadFromGPX(file,status=ARCHIVED)
    
  for file in frontiers:
    myAnimation.loadFromGPX(file,status=FRONTIER)

  for file in tracks:
    myAnimation.loadTracksFromCSV(file)

  for file in logs:
    myAnimation.loadLogsFromCSV(file)

  try:
    myAnimation.generateImages(tracing=True)
  except Exception, msg:
    print "Pb:",msg

  print 'That\'s all folks!'
  print 'Next step : mencoder "mf://map*.png" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'
  print 'Next step : mencoder "mf://@listPNG.txt" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1280:720'

