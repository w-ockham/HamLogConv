#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import csv
import datetime
import io
import re
import sys


def freq_to_band(freq_str):
    freq_table = [
        (0.1357,0.1378,'135kHz','2190m'),
        (0.472,0.479,'475kHz','630m'),
        (1.810,1.825,'1.9MHz','160m'),
        (1.9075,1.9125,'1.9MHz','160m'),
        (3.5,3.575,'3.5MHz','80m'),
        (3.599,3.612,'3.5MHz','80m'),
        (3.680,3.687,'3.5MHz','80m'),
        (3.702,3.716,'3.8MHz','80m'),
        (3.745,3.770,'3.8MHz','80m'),
        (3.791,3.805,'3.8MHz','80m'),
        (7.0,7.2,'7MHz','40m'),
        (10.000,10.150,'10MHz','30m'),
        (14.0,14.350,'14MHz','20m'),
        (18.0,18.168,'18MHz','17m'),
        (21.0,21.450,'21MHz','15m'),
        (24.0,24.990,'24MHz','12m'),
        (28.0,29.7,'28MHz','10m'),
        (50.0,54.0,'50MHz','6m'),
        (144.0,146.0,'144MHz','2m'),
        (430.0,440.0,'430MHz','70cm'),
        (1200.0,1300.0,'1200MHz','23cm'),
        (2400.0,2450.0,'2400MHz','13cm'),
        (5650.0,5850.0,'5600MHz','6cm'),
        (10000.0,10250.0,'10.1GHz','3cm'),
        (10450.0,10500.0,'10.4GHz','3cm'),
        (351.0,351.38125,'デジタル簡易(351MHz)',''),
        (421.0,454.19375,'特定小電力(422MHz)',''),
        (26.968,27.144,'CB(27MHz)',''),
        (26.968,27.144,'CB(27MHz)',''),
        (142.0,147.0,'デジタル小電力コミュニティ(142/146MHz)','')
        ]
    
    try:
        freq = float(freq_str)
    except Exception as e:
        freq = 0.0
        
    for (lower,upper,band,wlen) in freq_table:
        if freq >= lower and freq <= upper:
            return (band,wlen)
        
    return ('Out of the band','Out of the band')

def mode_to_airhammode(mode,freq_str):
    try:
        freq = float(freq_str)
    except Exception as e:
        freq = 0.0
       
    m = mode.upper()

    if m == 'SSB':
        if freq <= 7.2:
            return 'SSB(LSB)'
        else:
            return 'SSB(USB)'
    else:
        return m

def decodeHamlog(cols):
    m = re.match('(\w+)/(\w+)/(\w+)',cols[0])
    if m:
        operator = m.group(2)
        portable = m.group(1)
    else:
        m = re.match('(\w+)/(\w+)',cols[0])
        if m:
            operator = m.group(1)
            portable = m.group(2)
        else:
            operator = cols[0].strip()
            portable = ''
    
    m = re.match('(\d+)/(\d+)/(\d+)',cols[1])
    if m:
        if int(m.group(1)) >= 65:
            year = '19' + m.group(1)
        else:
            year = '20' + m.group(1)
        month = m.group(2)
        day = m.group(3)
    else:
        year = '20' + cols[1]
        month = ''
        day = ''

    m = re.match('(\d+):(\d+)(\w+)',cols[2])
    if m:
        hour = m.group(1)
        minute = m.group(2)
        fl = m.group(3).upper()
        if fl == 'U':
            timezone = '+0000'
        else:
            timezone = '+0900'
    else:
        hour = cols[2]
        minute = ''
        timezone = '+0900'

    tstr = year + '/' + month + '/' + day + ' ' + hour + ':' + minute + ' ' + timezone
    atime = datetime.datetime.strptime(tstr,'%Y/%m/%d %H:%M %z')
    utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))

    isotime = atime.isoformat()
    year = utime.year
    month = utime.month
    day = utime.day
    hour = utime.hour
    minute = utime.minute

    (band,_) = freq_to_band(cols[5])
    
    return {
        'callsign': cols[0],
        'operator': operator,
        'portable': portable,
        'isotime': isotime,
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'timezone': timezone,
        'rst_sent': cols[3],
        'rst_rcvd': cols[4],
        'freq': cols[5],
        'band': band,
        'mode': cols[6],
        'mode-airham': mode_to_airhammode(cols[6],cols[5]),
        'code': cols[7],
        'gl': cols[8],
        'qsl': cols[9],
        'name': cols[10],
        'qth': cols[11],
        'rmks1': cols[12],
        'rmks2': cols[13]
    }

    
def toAirHam(lcount, row, callsign, options):
    if lcount == 0:
        l= ["id","callsign","portable","qso_at","sent_rst",
            "received_rst","sent_qth","received_qth",
            "received_qra","frequency","mode","card",
            "remarks"]
        return l

    h = decodeHamlog(row)

    if options['QTH']=='rmks1':
        myqth = h['rmks1']
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        myqth = h['rmks2']
        comment = h['rmks1']
    elif options['QTH']=='user_defined':
        myqth = options['Location']
        comment = h['rmks1']
    else:
        myqth = ''
        comment = ''
        
    l = [
        "",
        h['operator'],
        h['portable'],
        h['isotime'],
        h['rst_sent'],
        h['rst_rcvd'],
        myqth,
        h['qth'],
        h['name'],
        h['band'],
        h['mode-airham'],
        h['qsl'],
        comment
    ]
    return l
    
def toSOTA(lcount, row, callsign, options):
    if lcount == 0:
        return None
    
    h = decodeHamlog(row)

    if options['QTH']=='rmks1':
        hisqth = h['rmks1']
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        hisqth = h['rmks2']
        comment = h['rmks1']
    else:
        hisqth = ''
        comment = ''
        
    l = [
        "V2",
        callsign,
        options['Summit'],
        '{day:02}/{month:02}/{year:02}'.format(day=h['day'], month=h['month'], year=h['year']),
        '{hour:02}:{minute:02}'.format(hour=h['hour'], minute=h['minute']),
        h['band'],
        h['mode'],
        h['callsign'],
        hisqth,
        ''
    ]
    return l
    
def main():
    cgitb.enable()

    form = cgi.FieldStorage()

    activation_call = form.getvalue('activation_call',None)
    chaser_call = form.getvalue('chaser_call',None)
    
    options = {
        'QTH': form.getvalue('QTH',None),
        'Location': form.getvalue('location',None),
        'Summit': form.getvalue('summit',None)
    }
    
    fileitem = form['filename']
    now  = datetime.datetime.now()
    fname = now.strftime("%Y-%m-%d-%H-%M")

    incharset = 'cp932'
    
    if activation_call:
        outcharset = "utf-8"
        fname = "sota-" + fname + ".csv"
        callsign = activation_call
        convfunc = toSOTA
    elif chaser_call:
        outcharset = "utf-8"
        fname = "sota-" + fname + ".csv"
        callsign = chaser_call
        convfunc = toSOTA
    else:
        outcharset = "utf-8"
        fname = "airhamlog-" + fname + ".csv"
        callsign = ''
        convfunc = toAirHam

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=outcharset)
    print('Content-Disposition: attachment;filename="%s"\n' % fname)
    #print('Content-Type: text/html\n')
    if fileitem.file:
        linecount = 0
        writer = csv.writer(sys.stdout,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)
        with io.TextIOWrapper(fileitem.file, encoding=incharset) as f:
            reader = csv.reader(f)
            for row in reader:
                if linecount > 100000:
                    break
                else:
                    if linecount == 0:
                        header = convfunc(linecount, row, callsign, options)
                        if header:
                            writer.writerow(header)
                        linecount += 1
                    writer.writerow(convfunc(linecount, row, callsign, options))
                    linecount += 1
    else:
        print('Content-type: text/html; charset=utf-8\n')
        print('<h1> File not found:%s' % fileitem)
        
if __name__ == '__main__':
    main()

