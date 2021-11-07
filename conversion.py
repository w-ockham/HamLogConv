#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import datetime
import json
from convutil import (
    sendSOTA_Both,
    sendSOTA_A,
    sendSOTA_C,
    sendWWFF,
    sendPOTA,
    sendADIF,
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
    cgitb.enable(display=0, logdir='/var/tmp/')

    form = cgi.FieldStorage()

    activation_call_both = form.getvalue('activation_call_both',None)
    activation_call = form.getvalue('activation_call',None)
    chaser_call = form.getvalue('chaser_call',None)
    pota_activation_call = form.getvalue('pota_activation_call',None)
    wwffoperator = form.getvalue('wwffoperator',None)
    gpx_trk_interval = form.getvalue('gpx_trk_interval',None)
    command = form.getvalue('command',None);
    
    options = {
        'Portable': form.getvalue('portable',''),
        'OmitPortable': form.getvalue('OmitPortable',''),
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
        'POTAOperator': form.getvalue('pota_operator',None),
        'Park': form.getvalue('park','')
    }

    if debug:
        fp = open('test.adif','rb')
        #activation_call_both = 'JL1NIE'
        pota_activation_call = 'JL1NIE'
        #options['QTH']='rmks1'
        options['myQTH']=''
        options['Portable']='portable'
        options['OmitPortable'] = ''
        options['Note']='rmks1'
        options['POTAOperator']= 'JL1NIE'
        options['POTAActivator']= 'JL1NIE/1'
        options['Park']= 'JAFF-0123,JA-0005'
        options['myQTH']='rmks2'
        options['QTH']='rmks1'
        #command = "ADIFCSVCheck"
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
        files, res  = sendADIF(fp, options, inchar, outchar)
        if command == "ADIFCSVCheck":
            print("Content-Type:application/json\n\n")
            print(json.dumps(res))
        else:
            fname = "adif-" + fname + ".zip"
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

