#!/usr/bin/env python
# -*- coding: iso-latin-1 -*-

# Generation of an animation film showing the development of geocaches in France
# Generation d'une animation montrant le développement des géocaches en France
#
# Copyright GarenKreiz at  geocaching.com or on  YouTube 
# Auteur    GarenKreiz sur geocaching.com ou sur YouTube
#
# Example:
#   http://www.youtube.com/watch?v=dQEG5hvDyGs
# Requires:
#   Python environment (tested with version 2.6.5)
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
import GPXParser

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

currentCountry = 'France'

# bounding rectangle of the country or state
# limites de la France metropolitaine + Corse
maxLatCountry = 51.08917 # dunes du Perroquet, Bray-Dunes près de Zuydcoote
minLatCountry = 41.33333 # cap di u Beccu, Iles Lavezzi, Corse
minLonCountry = -5.15083 # phare de Nividic, Ouessant
maxLonCountry =  9.56000 # plage Fiorentine, Alistro, Corse
scaleXY = (75,107)       # adapt to fit video size and preserve X/Y ratio
xSize,ySize=1120,1080    # size of output image

bigPixels = 1            # draw big pixels (2x2), otherwise (1x1)

# cache types
ARCHIVED    = 0
ACTIVE      = 1
UNAVAILABLE = 2
EVENT       = 3
TRACK       = 4

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
    
    if os.name <> 'posix':
      # Windows fonts
      fontPath = "c:\Windows\Fonts\ARIAL.TTF"
      fontPathFixed = "c:\Windows\Fonts\COURBD.TTF"
    else:
      # Linux fonts
      fontPath = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
      fontPathFixed = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"

    self.fontArial = ImageFont.truetype ( fontPath, 40 )
    self.fontArialMedium = ImageFont.truetype ( fontPath, 32 )
    self.fontArialSmall = ImageFont.truetype ( fontPath, 24 )
    self.fontFixed = ImageFont.truetype ( fontPathFixed, 32 )

    self.scaleX,self.scaleY = scaleX,scaleY
    self.XMinLon,self.XMaxLon = (minLon - 0.05),(maxLon + 0.15)
    self.YMinLat,self.YMaxLat = (minLat - 0.1),(maxLat + 0.1)
    
    self.LX = int((self.XMaxLon-self.XMinLon)*self.scaleX)
    self.LY = int((self.YMaxLat-self.YMinLat)*self.scaleY)

    if (self.LX < xSize) and (self.LY < ySize):
      self.LX,self.LY = xSize,ySize

    self.imResult = Image.new('RGB',(self.LX,self.LY),0)
    imDraw = ImageDraw.Draw(self.imResult)
    imDraw.text((30,5),   "Géocaches en France"             , font=self.fontArial,      fill="red")
    imDraw.text((35,50),  "animation: GarenKreiz"           , font=self.fontArialSmall, fill="red")
    imDraw.text((35,80),  "musique: Pedro Collares (Gothic)", font=self.fontArialSmall, fill="red")
    imDraw.text((36,110), "licence: CC BY-NC-SA"            , font=self.fontArialSmall, fill="red")

    self.allWpts = {}     # list of all GC waypoints

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
      return int(time.mktime(time.strptime(strTime, "%d/%m/%Y %H:%M:%SZ")))
    else:
      return 0
        
  def loadFromCSV(self,myCSV,minLon,maxLon,minLat,maxLat,geocacher=None):

    # Fields included in the GSAK view used to export to CSV
    #   Code,Cache Type,Note,Last4Logs,Last Log,Waypoint Name,Placed By,Placed,Last Found,Found,Country,Lat,Lon,Status,Url,Found by me,Owner Id

    print 'Processing',myCSV
    fInput = open(myCSV,'r')
    if geocacher <> None:
      geocacher = geocacher.upper()
    self.nAddedCaches = 0
    l = fInput.readline()
    while l <> '':
      fields = re.sub('[\n\r]*','',l)
      fields = re.sub('","','|',fields[1:-1])    # getting rid of all double quotes used by GSAK
      fields = string.split(fields,"|")
      (name,cacheType,note,last4logs,dateLastLog,wpName,placedBy,datePlaced,dateLastFound,found,country,latitude,longitude,status,url,dateFoundByMe,ownerId) = fields
      if name == "Code":                         # first line of headers in export file of GSAK
        l = fInput.readline()
        continue
      elif country <> currentCountry:
        print '!!! Pb cache outside',currentCountry,':',name
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
      if (lat > maxLat) or (lat < minLat) or \
         (lon > maxLon) or (lon < minLon) or (country <> currentCountry and country <> ''):
        print '!!! Pb point outside the drawing zone:',name
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

  def loadFromGPX(self,myGPX,minLon,maxLon,minLat,maxLat,status=ACTIVE):

    self.foundWpts = {}
    self.nAddedCaches = 0
      
    for p in myGPX.wpts:
      lat,lon = p.lat,p.lon

      try:
        country = p.attribs['groundspeak:country']
      except:
        country = ''

      if (lat > maxLat) or (lat < minLat) or \
         (lon > maxLon) or (lon < minLon) or (country <> 'France' and country <> ''):
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
    
  def generateFlash(self,myImage,LX,LY,nDays,cacheTime,nbCaches, distance):
    
    box = myImage.crop((0,0,self.LX,self.LY))
    imTemp = Image.new('RGB',(self.LX,self.LY),0)
    imTemp.paste(box,(0,0,self.LX,self.LY))

    for status in range(0,2):
      for i in range(0,self.flashLength):
        for (dx,dy) in self.flashAnimation[status][(i-self.flashCursor)%self.flashLength]:
          for (x,y) in self.flashList[status][i]:
            try:
              imTemp.putpixel((x+dx,y+dy),self.flashColor[status]) # yellow flash: cache activation, purple one for archiving
            except:
              print '!!! Pb writing pixel', nDays, x+dx, y+dy

    # next step on the animation of the flash
    self.flashCursor = (self.flashCursor - 1) % self.flashLength
    for status in range(0,2):
      self.flashList[status][self.flashCursor] = []

    imTempDraw = ImageDraw.Draw(imTemp)
    text = time.strftime("%d/%m/%Y",time.localtime(cacheTime))+" : %5d caches"%nbCaches
    if distance > 0:
      text = text+"- %.0f kms"%distance
    imTempDraw.text((200,self.LY-45), text, font=self.fontFixed, fill="blue")
    imTemp.save('map%04d.png'%nDays,"PNG")
  
  def generateImages(self, tracing):
    
    today = time.time()

    # misc counters
    nDays = 0
    nActiveCaches = 0
    nInactiveCaches = 0
    nCaches = 0
    
    cacheTimes = self.allWpts.keys()
    cacheTimes.sort()

    # initialize the time of the current frame to the first date
    previousTime = cacheTimes[0]

    # variables to display the geocacher's moves
    latOld,lonOld = 0.0,0.0 
    xOld,yOld = 0,0
    distance = 0
    
    for cacheTime in cacheTimes:
      # don't display future dates corresponding to future events
      if cacheTime > today:
          cacheTime = today
          break
        
      # generate intermediate images for each days between last cache day and current day
      for catchingTime in range(previousTime+24*3600, cacheTime, 24*3600):
          nDays= nDays + 1
          self.generateFlash(self.imResult,self.LX,self.LY,nDays,catchingTime,nCaches,distance)

      nDays = nDays + 1
      if tracing:
        print '.',
        
      for (lat,lon,name,status) in self.allWpts[cacheTime]:
        x = int(self.scaleX*(lon-self.XMinLon))
        y = int(self.scaleY*(self.YMaxLat-lat))
        if status == UNAVAILABLE or status == ACTIVE:
          nActiveCaches += 1
          self.flashList[1][self.flashCursor].append((x,y))
        elif status == ARCHIVED:
          nInactiveCaches += 1
          self.flashList[0][self.flashCursor].append((x,y))

        if status == ACTIVE or status == EVENT:          # active caches or events
          nCaches = nCaches + 1
        try:
          if status == TRACK:                            # drawing moves of a geocacher
            draw = ImageDraw.Draw(self.imResult)
            if (xOld,yOld) <> (0,0):
              draw.line([(xOld, yOld),(x,y)], self.cacheColor[TRACK])
              distance += getDistance(latOld,lonOld,lat,lon)
            del draw
            xOld,yOld = x,y
            latOld,lonOld = lat,lon
          else:
            self.drawPoint(status,x,y)
        except Exception, msg:
          print '!!! Pb point outside the drawing area:',lat, lon, name, x, y, msg

      self.generateFlash(self.imResult,self.LX,self.LY,nDays,cacheTime,nCaches, distance)

      previousTime = cacheTime

    # display the final situation during a few seconds
    for i in range(nDays,nDays+100):
    	self.generateFlash(self.imResult,self.LX,self.LY,i,cacheTime,nCaches, distance)

    # final view of all caches
    self.imResult.save('Geocaching_France.jpg')
    self.imResult.save('Geocaching_France.png',"PNG")
    print ''
    print 'Processed ', nCaches, 'caches'
    print 'Processed ', nActiveCaches, 'active caches'
    print 'Processed ', nInactiveCaches, 'inactive caches'
    
if __name__=='__main__':
  
  myAnimation = GCAnimation(scaleXY,minLonCountry,maxLonCountry,minLatCountry,maxLatCountry)

  nbArgs = len(sys.argv)
  if nbArgs == 1:
    print 'Usage: python generationAnimation.py <active_caches.gpx> [ ... <archived_caches.gpx> ]'
    print 'Usage: python generationAnimation.py <gsak_extract.csv> [ <name of geocacher> ]'
  else:
    if sys.argv[1][-4:].lower() == '.gpx':
      # process GPX containing active cache
      for i in range(1,nbArgs):
        try:
          print "Processing ", sys.argv[i]
          myGPX = GPXParser.GPXParser(sys.argv[i])
          print 'Waypoints found :',len(myGPX.wpts)
          if nbArgs > 2 and i == nbArgs-1:
            myAnimation.loadFromGPX(myGPX,minLonCountry,maxLonCountry,minLatCountry,maxLatCountry,status=ARCHIVED)
          else:
            myAnimation.loadFromGPX(myGPX,minLonCountry,maxLonCountry,minLatCountry,maxLatCountry,status=ACTIVE)
        except Exception, msg:
          print '!!! Pb parsing file',sys.argv[i], msg
          sys.exit()
    else:
      if nbArgs > 2:
        myAnimation.loadFromCSV(sys.argv[1],minLonCountry,maxLonCountry,minLatCountry,maxLatCountry,geocacher=sys.argv[2])
      else:
        myAnimation.loadFromCSV(sys.argv[1],minLonCountry,maxLonCountry,minLatCountry,maxLatCountry,geocacher=None)

  myAnimation.generateImages(tracing=True)

  print 'That\'s all folks!'
  print 'Next step : mencoder "mf://map*.png" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1120:1080'
  print 'Next step : mencoder "mf://@listPNG.txt" -mf fps=24 -o Film.avi -ovc lavc -lavcopts vcodec=mpeg4 -vf scale=1120:1080'
