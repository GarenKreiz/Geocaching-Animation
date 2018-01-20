#!/usr/bin/env python
import os, re
 
class GPXTrack:
   def __init__(self):
      self.attribs = {}
      self.wpts = []
      self.segs = []
      self._bbox_ = None
      
   def bbox(self, latMin=None, latMax=None, lonMin=None,lonMax=None):
     if latMin == None:
       return self._bbox_
     self._bbox_ = (latMin, latMax, lonMin, lonMax)
 
   def from_string(self, c):
      f = re.search("<trk(?P<opts>.*?)>(?P<content>.*?)</trk>", c, re.DOTALL+re.I)   
      opts = re.findall(re.compile(".*?=\".*?\"", re.DOTALL), f.group("opts"))
      for opt in opts:
         n, v = opt.split("=")    
         v = v.strip()
         if v.startswith("\"") and v.endswith("\""): v = v[1:-1]
         self.attribs[n.strip()] = v
 
      segs = re.findall(re.compile("<trkseg>.*?</trkseg>", re.DOTALL+re.I), f.group("content"))   
      cont = re.sub(re.compile("<trkseg>.*</trkseg>", re.DOTALL+re.I), "",f.group("content"))
 
      attrib = re.findall(re.compile("<(.+?)>(.*?)</(.+?)>", re.DOTALL+re.I), cont)   
      for a in attrib:
         self.attribs[a[0].strip()] = a[1].strip()    
 
      for seg in segs:
         newSeg = GPXTrack()
         index = seg.find("<trkpt", 0)
         latMin, latMax = 100.0, -100.0
         lonMin, lonMax = 181.0, -181.0
         while (index <> -1):
            indexFin = seg.index(">",index)
            w = GPXWaypoint()
            w.from_string(seg[index:indexFin+1]) 
            self.wpts.append(w)
            newSeg.wpts.append(w)
            x,y = w.xy()
            latMin, latMax = min(x,latMin), max(x, latMax)
            lonMin, lonMax = min(y,lonMin), max(y, lonMax)
            index = seg.find("<trkpt", indexFin)
         newSeg.bbox(latMin,latMax,lonMin,lonMax)
         self.segs.append(newSeg)
 
   def __repr__(self):
      r = "Track:   "+self.attribs.__repr__()+"\nPoints: "
      for w in self.wpts:
         r += w.__repr__() 
      return r+"\n"   

class GPXWaypoint:
   #lon = 0 # -180.0 - +180.0
   #lat = 0 # -90.0 - +90.0
   #attribs = {}
   def __init__(self, lon=0, lat=0):
      self.lon, self.lat = lon, lat 
      self.attribs={}
   def from_string(self, c):
      f = re.search("<(trk|w)pt(?P<opts>.*?)>(?P<content>.*?)", c, re.DOTALL+re.I)
      # print "Wpt"
      if not f: return 1
      c = re.compile(".*?=\".*?\"", re.DOTALL)
      # print c
      # print f.group("opts")
      opts = re.findall(re.compile(".*?=\".*?\"", re.DOTALL), f.group("opts"))
      # print "Wpt from string next"

      for o in opts:
         n, v = o.split("=")    
         v = v.strip()
         if v.startswith("\"") and v.endswith("\""): v = v[1:-1]
         if n.strip() == "lon": self.lon = float(v)
         elif n.strip() == "lat": self.lat = float(v)
      attrib = re.findall(re.compile("<(.+?)>(.*?)</(.+?)>", re.DOTALL+re.I), f.group("content"))   
      for a in attrib:
         self.attribs[a[0].strip()] = a[1].strip()    
 
   def __str__(self):
      return "WP (lon="+str(self.lon)+", lat="+str(self.lat)+")\n  Attributes: "+self.attribs.__repr__()+"\n"
   def __repr__(self):
      return self.__str__()
   def xy(self):
       return(self.lat,self.lon)
 
 
 
class GPXRoute:
   #wps = [] # list of GPXWaypoints    
   #attribs = {}
   def __init__(self):
      self.wps = [] # list of GPXWaypoints    
      self.attribs = {}
      pass    
 
class GPXParser:
   #trcks  = [] # list of GPXTrack objects    
   #wpts = [] # list of GPXWp objects    
   #rts  = [] # list of GPXRoute objects    
   def __init__(self, filename):    
      self.attribs={}
      if not filename.endswith(".gpx"):    
         print "Warning: filename does not end on .gpx..."
      self.file = filename    
      f = open(filename, "r")
      content = f.read(); f.close()
      # print "Parsing start"
      self.init_from_string(content)
      # print "Parsing end"
 
   def init_from_string(self, c):
      self.trcks, self.wpts, self.rts = [], [], []    
      gpx = re.search("<gpx(?P<opts>.*?)>(?P<content>.*?)</gpx>", c,re.DOTALL+re.I)
      # print "Init from string"
      if not gpx: return 1
      # print gpx.group("opts")
      #gpx_opts = re.findall(re.compile(".*?=\".*?\"", re.DOTALL), gpx.group("opts"))
      #print "Init from string next"
      #for gopt in gpx_opts:
      #   n, v = gopt.split("=")    
      #   v = v.strip()
      #   if v.startswith("\"") and v.endswith("\""): v = v[1:-1]
      #   self.attribs[n.strip()] = v

      # print gpx
      # print gpx.group("content")
      # print "Init from string next"
      # Waypoints
      gpx_wpts = re.findall(re.compile("<wpt.*?>.*?</wpt>", re.DOTALL+re.I), gpx.group("content"))
      # print "Init from string next"
      # print gpx_wpts
      for wp in gpx_wpts:
         wpt = GPXWaypoint()
         wpt.from_string(wp)
         self.wpts.append(wpt)
 
      # print "Init from string next"
      # Tracks   
      gpx_trks = re.findall(re.compile("<trk.*?>.*?</trk>", re.DOTALL+re.I), gpx.group("content"))   
      for trk in gpx_trks:
         t = GPXTrack()
         t.from_string(trk)
         print len(t.segs)
         self.trcks.append(t)
      # print "Init from string end"
 
if __name__=='__main__':
   import sys
   
   # parser = GPXParser("rondane06_tracks.gpx")    
   # parser = GPXParser("test.gpx")    

   parser = GPXParser(sys.argv[1])

   for p in parser.wpts:
      print p
      
