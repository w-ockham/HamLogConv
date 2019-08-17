#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import csv
import datetime
import io
import re
import sys
import zipfile

debug = False
#debug = True

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

def mode_to_SOTAmode(mode):
    mode_table = [
        ('CW',['CW']),
        ('SSB',['SSB']),
        ('FM',['FM']),
        ('AM',['AM']),
        ('DATA',['RTTY','RTY','PSK','PSK31','PSK-31','DIG','DATA',
                 'JT9','JT65','FT8','FT4','FSQ']),
        ('DV',['DV','FUSION','DSTAR','D-STAR','DMR','C4FM'])]
    
    for smode,pat in mode_table:
        if mode.upper() in pat:
            return smode
    return 'OTHER'

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

    (band,wlen) = freq_to_band(cols[5])
    
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
        'band-wlen': wlen,
        'mode': cols[6],
        'mode-airham': mode_to_airhammode(cols[6],cols[5]),
        'mode-sota': mode_to_SOTAmode(cols[6]),
        'code': cols[7],
        'gl': cols[8],
        'qsl': cols[9],
        'name': cols[10],
        'qth': cols[11],
        'rmks1': cols[12],
        'rmks2': cols[13]
    }
    
def toAirHam(lcount, row, options):
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

def get_ref(str):
    r = { 'SOTA':'', 'WWFF':'' }
    l = re.split('[,\s]', str)
    for ref in l:
        m = re.match('(\w+FF-\d+)',ref)
        if m:
            r['WWFF'] = m.group(1)
        m = re.match('(\w+/\w+-\d+)',ref)
        if m:
            r['SOTA'] = m.group(1)
    return r

def toSOTA(row, callsign, options):
    h = decodeHamlog(row)

    if options['QTH']=='rmks1':
        hisqth = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        hisqth = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        hisqth = {'SOTA':''}
        comment = ''
    
    date = '{day:02}/{month:02}/{year:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])

    date2 = '{year:02}{month:02}{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])
    
    l = [
        "V2",
        callsign,
        options['Summit'],
        date,
        '{hour:02}:{minute:02}'.format(hour=h['hour'], minute=h['minute']),
        h['band'],
        h['mode-sota'],
        h['callsign'],
        hisqth['SOTA'],
        ''
    ]
    return (date2,hisqth['SOTA']!='',l)

def adif(key, value):
    adif_fields = [
        ('STATION_CALLSIGN','WWFFActivator'),
        ('CALL','callsign'),
        ('QSO_DATE','date'),
        ('TIME_ON','time'),
        ('BAND','band-wlen'),
        ('MODE','mode'),
        ('RST_SENT','rst_sent'),
        ('RST_RCVD','rst_rcvd'),
        ('MY_SIG','mysig'),
        ('MY_SIG_INFO','mysiginfo'),
        ('SIG','sig'),
        ('SIG_INFO','siginfo'),
        ('MY_SOTA_REF','mysotaref'),
        ('OPERATOR','WWFFOperator'),
        ('PROGRAMID','programid'),
        ('ADIF_VER','adifver')
    ]
    for (field,k) in adif_fields:
        if key == k:
            f ='<' + field + ':' + str(len(value)) + '>' + value
            return f
    f ='<COMMENT:' + str(len(value)) + '>' + value
    return f
        
def toWWFF(row, options):
    h = decodeHamlog(row)

    if options['QTH']=='rmks1':
        hisref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        hisref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        hisref = {'SOTA':'','WWFF':''}
        comment = ''
        
    date = '{year:02}{month:02}{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])
    
    date2 = '{year:02}-{month:02}-{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])
    
    wwffref = options['WWFFRef']

    l = [
        adif('WWFFActivator',options['WWFFActivator']),
        adif('callsign',h['callsign']),
        adif('date',date),
        adif('time',
             '{hour:02}{minute:02}'.format(
                 hour=h['hour'], minute=h['minute'])),
        adif('band-wlen',h['band-wlen']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
        adif('mysig','WWFF'),
        adif('mysiginfo',options['WWFFRef'])
        ]
    
    if hisref['WWFF'] != '':
        l+= [adif('sig','WWFF'),adif('siginfo',hisref['WWFF'])]

    if None and hisref['SOTA'] != '':
        l+= [adif('mysotaref',hisref['SOTA'])]

    l+= [adif('WWFFOperator',options['WWFFOperator']),'<EOR>']
    
    return (date2,wwffref,l)

def sendAirHamLog(fp, fname, options, inchar, outchar):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=outchar)
    print('Content-Disposition: attachment;filename="%s"\n' % fname)
    linecount = 0
    writer = csv.writer(sys.stdout,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    with io.TextIOWrapper(fp, encoding=inchar) as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                if linecount == 0:
                    writer.writerow(toAirHam(linecount, row, options))
                    linecount += 1
                writer.writerow(toAirHam(linecount, row, options))
                linecount += 1

def writeCSV(files,zipfname):
    print('Content-Disposition: attachment;filename="%s"\n' % zipfname)
    buff = io.BytesIO()
    z = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    for k,v in files.items():
        z.writestr(k, v)
    z.close()
    sys.stdout.flush()
    sys.stdout.buffer.write(buff.getvalue())
        
def sendSOTA_A(fp, zipfname, callsign, options, inchar, outchar):
    prefix = 'sota'
    prefix2 = 'sota-s2s-'
    fname = ''
    files = {}
    linecount = 0

    outstr = io.StringIO()
    writer = csv.writer(outstr,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    outstr_s2s = io.StringIO()
    writer_s2s = csv.writer(outstr_s2s,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

    with io.TextIOWrapper(fp, encoding=inchar) as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (fn,s2s,l) = toSOTA(row, callsign, options)
                if linecount == 0:
                    fname = fn
                    
                if fn == fname:
                    writer.writerow(l)
                    if s2s:
                        writer_s2s.writerow(l)
                    linecount += 1
                else:
                    name = prefix + fname + '.csv'
                    files.update({name : outstr.getvalue()})

                    s2sbuff = outstr_s2s.getvalue()
                    if len(s2sbuff) >0:
                        name2 = prefix2 + fname + '.csv'
                        files.update({name2 : s2sbuff})
                        
                    outstr = io.StringIO()
                    writer = csv.writer(outstr,delimiter=',',
                                        quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(l)

                    outstr_s2s = io.StringIO()
                    writer_s2s = csv.writer(outstr_s2s,delimiter=',',
                                            quoting=csv.QUOTE_MINIMAL)
                    if s2s:
                        writer_s2s.writerow(l)
                    fname = fn

        name = prefix + fname + '.csv'
        files.update({name : outstr.getvalue()})

        s2sbuff = outstr_s2s.getvalue()
        if len(s2sbuff) >0:
            name2 = prefix2 + fname + '.csv'
            files.update({name2 : s2sbuff})

    writeCSV(files,zipfname)    

def sendSOTA_C(fp, zipfname, callsign, options, inchar, outchar):
    prefix = 'sota'
    fname = ''
    files = {}
    linecount = 0

    outstr = io.StringIO()
    writer = csv.writer(outstr,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)

    with io.TextIOWrapper(fp, encoding=inchar) as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (fn,s2s,l) = toSOTA(row, callsign, options)
                if linecount == 0:
                    fname = fn
                    
                if fn == fname:
                    writer.writerow(l)
                    linecount += 1
                else:
                    name = prefix + fname + '.csv'
                    files.update({name : outstr.getvalue()})

                    outstr = io.StringIO()
                    writer = csv.writer(outstr,delimiter=',',
                                        quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(l)
                    fname = fn

        name = prefix + fname + '.csv'
        files.update({name : outstr.getvalue()})

    writeCSV(files,zipfname)

def sendWWFF(fp, options, inchar, outchar):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=outchar)

    linecount = 0
    writer = csv.writer(sys.stdout,delimiter=' ',
                        quoting=csv.QUOTE_MINIMAL)
    with io.TextIOWrapper(fp, encoding=inchar) as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (date,ref,l) = toWWFF(row,options)
                if linecount == 0:
                    act_call = options['WWFFActivator']
                    fname = act_call.replace('/','-') + '@' + ref + ' '+ date +'.adif'
                    print('Content-Disposition: attachment;filename="%s"\n'
                          % fname)
                    print('ADIF Export from HAMLOG by JL1NIE')
                    print(adif('programid','FCTH'))
                    print(adif('adifver','3.0.6'))
                    print('<EOH>')
                writer.writerow(l)
                linecount += 1
    
def main():
    cgitb.enable()

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
    else:
        fileitem = form['filename']
        fp = fileitem.file
        
    now  = datetime.datetime.now()
    fname = now.strftime("%Y-%m-%d-%H-%M")

    inchar = 'cp932'

    if activation_call:
        outchar = "utf-8"
        callsign = activation_call
        fname = "sota-" + fname + ".zip"
        sendSOTA_A(fp, fname, callsign, options, inchar, outchar)
    elif chaser_call:
        outchar = "utf-8"
        callsign = chaser_call
        fname = "sota-" + fname + ".zip"
        sendSOTA_C(fp, fname, callsign, options, inchar, outchar)
    elif wwffoperator:
        outchar = "utf-8"
        sendWWFF(fp, options, inchar, outchar)
    else:
        outchar = "utf-8"
        fname = "airhamlog-" + fname + ".csv"
        sendAirHamLog(fp,fname,options,inchar,outchar)
        
if __name__ == '__main__':
    main()

