#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime,timedelta
import io
import sys
import xml.etree.ElementTree as ET

ns = {
    'gpx0':"http://www.topografix.com/GPX/1/0",
    'gpx1':"http://www.topografix.com/GPX/1/1",
    'ks':"http://www.kashmir3d.com/namespace/kashmir3d"
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

    if not 'version' in root.attrib:
        if gpxver == 'GPX1.1':
            root.attrib['version'] = '1.1'
        else:
            root.attrib['version'] = '1.0'

    prev = datetime(1900,1,1,0,0,0)
    delta = timedelta(seconds = interval)
    
    if gpxver == 'GPX1.1':
    #for Garmin Instinct and ohter.
        for trk in root.findall('./gpx1:trk',ns):
            for ext in trk.findall('./gpx1:extensions',ns):
                trk.remove(ext)

        for trkseg in trk.findall('./gpx1:trkseg',ns):
            for trkpt in trkseg.findall('./gpx1:trkpt',ns):
                now = iso2dt(trkpt.find('gpx1:time',ns).text)
                if now - prev > delta:
                    for ext in trkpt.findall('./gpx1:extensions',ns):
                        trkpt.remove(ext)
                    prev = now
                else:
                    trkseg.remove(trkpt)

        ET.register_namespace('',ns['gpx1'])
                
    elif gpxver == 'GPX1.0':
    #for Geographica
        for trk in root.findall('./gpx0:trk',ns):
            for trkseg in trk.findall('./gpx0:trkseg',ns):
                for trkpt in trkseg.findall('./gpx0:trkpt',ns):
                    now = iso2dt(trkpt.find('gpx0:time',ns).text)
                    if now - prev > delta:
                        for r in trkpt.findall('./gpx0:speed',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:trueHeading',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:magneticHeading',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:gpsHeading',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:haccuracy',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:vaccuracy',ns):
                            trkpt.remove(r)
                        for r in trkpt.findall('./gpx0:internetconnect',ns):
                            trkpt.remove(r)
                        prev = now
                    else:
                        trkseg.remove(trkpt)
        ET.register_namespace('',ns['gpx0'])

    return gpxver

def sendGPX(fp, fname, interval, inchar, outchar):
    ET.register_namespace('gpx0',ns['gpx0'])
    ET.register_namespace('gpx1',ns['gpx1'])
    ET.register_namespace('kashmir3d',ns['ks'])

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
        
        gpxver = trim_trk(root,int(interval))
        sys.stdout.write(ET.tostring(root,encoding = outchar).decode(outchar))
        print('')
        
if __name__ == '__main__':
    argv = sys.argv
    fp = open(argv[1],'rb')
    sendGPX(fp,'result.xml',60,"UTF-8","UTF-8")
