#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime,timedelta
import io
import sys
from lxml import etree as ET

ns = {
    'gpx0':"http://www.topografix.com/GPX/1/0",
    'gpx1':"http://www.topografix.com/GPX/1/1",
    }
nsmap = {
    None: "http://www.topografix.com/GPX/1/1",
    'xsi':"http://www.w3.org/2001/XMLSchema-instance",
    }
    
def iso2dt(iso_str):
    dt = None
    try:
        dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        try:
            dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            pass
    return dt

def trim_trk(root,interval):

    if root.findall('./gpx0:trk',ns):
        gpxver = 'GPX1.0'
    elif root.findall('./gpx1:trk',ns):
        gpxver = 'GPX1.1'
    else:
        gpxver = None

    prev = datetime(1900,1,1,0,0,0)
    delta = timedelta(seconds = interval)
    
    if gpxver == 'GPX1.0':
        prfx = './gpx0:'
    elif gpxver == 'GPX1.1':
        prfx = './gpx1:'
    else:
        prfx = './'
        
    gpx = ET.Element('gpx',nsmap = nsmap)
    xsins = "{%s}" % nsmap['xsi']
    gpx.attrib['creator'] = "GPX for SOTAmap"
    gpx.attrib[xsins+'schemaLocation'] = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"                               
    gpx.attrib['version'] = "1.1"
    
    for trk in root.findall(prfx+'trk',ns):
        new_trk = ET.SubElement(gpx,'trk')
        new_name = ET.SubElement(new_trk,'name')
        new_name.text = trk.find(prfx+'name',ns).text
        
        for trkseg in trk.findall(prfx+'trkseg',ns):
            new_trkseg = ET.SubElement(new_trk,'trkseg')
            for trkpt in trkseg.findall(prfx+'trkpt',ns):
                now = iso2dt(trkpt.find(prfx+'time',ns).text)
                if now - prev > delta:
                    new_trkpt = ET.SubElement(new_trkseg,'trkpt')
                    new_trkpt.attrib['lat'] = trkpt.attrib.get('lat','')
                    new_trkpt.attrib['lon'] = trkpt.attrib.get('lon','')
                    new_ele = ET.SubElement(new_trkpt,'ele')
                    new_ele.text = trkpt.find(prfx+'ele',ns).text
                    new_time = ET.SubElement(new_trkpt,'time')
                    new_time.text = trkpt.find(prfx+'time',ns).text
                    prev = now
    return gpx

def sendGPX(fp, fname, interval, inchar, outchar):
    ET.register_namespace('gpx0',ns['gpx0'])
    ET.register_namespace('gpx1',ns['gpx1'])

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=outchar, errors="backslashreplace")
    print('Content-Disposition: attachment;filename="%s"\n' % fname)
    print('<?xml version="1.0" encoding="UTF-8" ?>')
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        lines = f.readlines()
        try:
            root = ET.fromstringlist(lines)
        except Exception as e:
            print(e)
            print(lines)
            return
        
        gpx = trim_trk(root,int(interval))
        sys.stdout.write(ET.tostring(gpx,encoding = outchar).decode(outchar))
        print('')
        
if __name__ == '__main__':
    argv = sys.argv
    fp = open(argv[1],'rb')
    sendGPX(fp,'result.xml',60,"UTF-8","UTF-8")
