#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import datetime
from convutil import (
    sendSOTA_Both,
    sendSOTA_A,
    sendSOTA_C,
    sendWWFF,
    sendPOTA,
    sendAirHamLog,
    decodeHamlog,
    writeZIP,
    writeTXT,
    emitError
)

from trimgpx import (
    sendGPX
)

debug = False
#debug = True


def main():
    #cgitb.enable()

    form = cgi.FieldStorage()

    activation_call_both = form.getvalue('activation_call_both',None)
    activation_call = form.getvalue('activation_call',None)
    chaser_call = form.getvalue('chaser_call',None)
    pota_activation_call = form.getvalue('pota_activation_call',None)
    wwffoperator = form.getvalue('wwffoperator',None)
    gpx_trk_interval = form.getvalue('gpx_trk_interval',None)
    
    options = {
        'Portable': form.getvalue('portable',''),
        'QTH': form.getvalue('QTH',''),
        'hisQTH': form.getvalue('hisQTH',''),
        'hisQTHopt': form.getfirst('hisQTHopt',''),
        'myQTH': form.getvalue('myQTH',''),
        'Note': form.getvalue('Note',''),
        'Summit': form.getvalue('summit',''),
        'Location': form.getvalue('location',''),
        'WWFFOperator': form.getvalue('wwffoperator',''),
        'WWFFActivator': form.getvalue('wwffact_call',''),
        'WWFFRef': form.getvalue('wwffref',''),
        'SOTAActivator': activation_call,
        'POTAActivator': pota_activation_call,
        'Park': form.getvalue('park','')
    }

    if debug:
        fp = open('sample.csv','rb')
        activation_call_both = 'JL1NIE'
        options['QTH']='rmks1'
        options['myQTH']='rmks2'
        options['Portable']='portable'
        options['Note']='rmks1'
        #options['WWFFOperator']= wwffoperator
        #options['WWFFActivator']=wwffoperator+'/1'
        #options['WWFFRef']= 'JAFF-0123'
        #wwffoperator=''
        #fp = open('tmp/test.gpx','rb')
        #gpx_trk_interval = '60'
    else:
        try:
            fileitem = form['filename']
        except KeyError as e:
            emitError("Please input HAMLOG csv file.")
            return
        fp = fileitem.file
        
        
    now  = datetime.datetime.now()
    fname = now.strftime("%Y-%m-%d-%H-%M")

    inchar = 'cp932'

    if activation_call_both:
        outchar = "utf-8"
        callsign = activation_call_both
        fname = "sota-" + fname + ".zip"
        files = sendSOTA_Both(fp, decodeHamlog, callsign, options,
                              inchar, outchar)
        writeZIP(files,fname)
                
    elif activation_call:
        outchar = "utf-8"
        callsign = activation_call
        fname = "sota-" + fname + ".zip"
        files = sendSOTA_A(fp, decodeHamlog, callsign, options,
                           inchar, outchar)
        writeZIP(files,fname)
        
    elif chaser_call:
        outchar = "utf-8"
        callsign = chaser_call
        fname = "sota-" + fname + ".zip"
        files = sendSOTA_C(fp, decodeHamlog, callsign, options,
                           inchar, outchar)
        writeZIP(files,fname)

    elif pota_activation_call:
        outchar = "utf-8"
        files = sendPOTA(fp, options, inchar, outchar)
        fname = "pota-" + fname + ".zip"
        writeZIP(files,fname)
        
    elif wwffoperator:
        outchar = "utf-8"
        files = sendWWFF(fp, decodeHamlog, options, inchar, outchar)
        writeTXT(files)

    elif gpx_trk_interval:
        inchar = "utf-8"
        outchar = "utf-8"
        fname = "sotagpx-" + fname + ".gpx"
        res = sendGPX(fp, fname, gpx_trk_interval, inchar, outchar)

    else:
        outchar = "utf-8"
        fname = "airhamlog-" + fname + ".csv"
        res = sendAirHamLog(fp, fname, decodeHamlog, options, inchar, outchar)
        
if __name__ == '__main__':
    main()

