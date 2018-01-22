#!/usr/bin/env python
# -*- coding: utf-8 -*-

# csv2loc
#
#   conversion d'une extraction GCSAK en CSV au format LOC
# 

import string
import sys
import re

locString = """
<?xml version="1.0" encoding="UTF-8"?>
<loc version="1.0" src="GSAK">
"""
wptString = """
<waypoint>
 <name id="%s"><![CDATA[%s]]></name>
 <coord lat="%s" lon="%s"/>
 <type>Geocache</type>
 <link text="Waypoint Details">%s</link>
</waypoint>
"""
endString = """
</loc>
"""

print locString

with open(sys.argv[1],"r") as fInput:
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
    l = fInput.readline()
    if name <> "Code GC":
      print wptString%(name,wpName,latitude,longitude,url)

print endString
  
