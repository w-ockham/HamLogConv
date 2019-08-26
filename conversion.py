#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import datetime
from convutil import (
    sendSOTA_A,
    sendSOTA_C,
    sendWWFF,
    sendAirHamLog,
    decodeHamlog,
    writeZIP,
    writeTXT,
    emitError
)

debug = False
#debug = True


def main():
    #cgitb.enable()

    form = cgi.FieldStorage()

    activation_call = form.getvalue('activation_call',None)
    chaser_call = form.getvalue('chaser_call',None)
    wwffoperator = form.getvalue('wwffoperator',None)
    
    options = {
        'QTH': form.getvalue('QTH',''),
        'Location': form.getvalue('location',''),
        'Summit': form.getvalue('summit',''),
        'WWFFOperator': form.getvalue('wwffoperator',''),
        'WWFFActivator': form.getvalue('wwffact_call',''),
        'WWFFRef': form.getvalue('wwffref','')
    }

    if debug:
        fp = open('sample.csv','rb')
        wwffoperator = 'JL1NIE'
        options['QTH']='rmks1'
        options['WWFFOperator']= wwffoperator
        options['WWFFActivator']=wwffoperator+'/1'
        options['WWFFRef']= 'JAFF-0123'
        wwffoperator=''
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

    if activation_call:
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
        
    elif wwffoperator:
        outchar = "utf-8"
        files = sendWWFF(fp, decodeHamlog, options, inchar, outchar)
        writeTXT(files)
    else:
        outchar = "utf-8"
        fname = "airhamlog-" + fname + ".csv"
        res = sendAirHamLog(fp, fname, decodeHamlog, options, inchar, outchar)
        
if __name__ == '__main__':
    main()

