#!/usr/bin/env python3
# coding: utf-8
import csv
import datetime
import io
import re
import sys
import zipfile

def writeZIP(files,zipfname):
    print('Content-type:application/octet-stream; name="{}"'.format(zipfname))
    print('Content-Disposition:attachment; filename="{}"\r\n'.format(zipfname))
    buff = io.BytesIO()
    z = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
    for k,v in files.items():
        z.writestr(k, v)
    z.close()
    sys.stdout.flush()
    sys.stdout.buffer.write(buff.getvalue())

def writeTXT(files):
    for k,v in files.items():
        print('Content-Disposition:attachment; filename="{}"\r\n'.format(k))
        print(v)

def emitError(txt):
    print("Content-Type:text/html\n\n")
    print("<h4><font color=\"#ff0000\"> Error: {}</font></h4>".format(txt))
    print("<p><input type=\"button\" value=\"back\" onclick=\"history.back()\"></p>")
            
freq_table = [
    (0.1357,0.1378,'135kHz','VLF','2190m'),
    (0.472,0.479,'475kHz','VLF','630m'),
    (1.8,1.825,'1.9MHz','1.8MHz','160m'),
    (1.9,1.9125,'1.9MHz','1.8MHz','160m'),
    (3.5,3.575,'3.5MHz','3.5MHz','80m'),
    (3.599,3.612,'3.5MHz','3.5MHz','80m'),
    (3.680,3.687,'3.5MHz','3.5MHz','80m'),
    (3.702,3.716,'3.8MHz','3.5MHz','80m'),
    (3.745,3.770,'3.8MHz','3.5MHz','80m'),
    (3.791,3.805,'3.8MHz','3.5MHz','80m'),
    (7.0,7.2,'7MHz','7MHz','40m'),
    (10.000,10.150,'10MHz','10MHz','30m'),
    (14.0,14.350,'14MHz','14MHz','20m'),
    (18.0,18.168,'18MHz','18MHz','17m'),
    (21.0,21.450,'21MHz','21MHz','15m'),
    (24.0,24.990,'24MHz','24MHz','12m'),
    (28.0,29.7,'28MHz','28MHz','10m'),
    (50.0,54.0,'50MHz','50MHz','6m'),
    (144.0,146.0,'144MHz','144MHz','2m'),
    (430.0,440.0,'430MHz','433MHz','70cm'),
    (1200.0,1300.0,'1200MHz','1240MHz','23cm'),
    (2400.0,2450.0,'2400MHz','2.3GHz','13cm'),
    (5650.0,5850.0,'5600MHz','5.6GHz','6cm'),
    (10000.0,10250.0,'10.1GHz','10GHz','3cm'),
    (10450.0,10500.0,'10.4GHz','10GHz','3cm'),
    (351.0,351.38125,'デジタル簡易(351MHz)','',''),
    (421.0,454.19375,'特定小電力(422MHz)','',''),
    (26.968,27.144,'CB(27MHz)','',''),
    (26.968,27.144,'CB(27MHz)','',''),
    (142.0,147.0,'デジタル小電力コミュニティ(142/146MHz)','','')
]

def band_to_freq(band_str, is_sota = False):
    for (_, _, f_air, f_sota, b) in freq_table:
        b1 = b.upper()
        b2 = band_str.upper()
        if b1 == b2:
            if is_sota:
                return f_sota
            else:
                return f_air
    return(None)
    
def freq_to_band(freq_str):
    
    try:
        freq = float(freq_str)
    except Exception as e:
        freq = 0.0
        
    for (lower,upper,band_air,band_sota,wlen) in freq_table:
        if freq >= lower and freq <= upper:
            return (band_air,band_sota,wlen)
        
    return ('Out of the band','Out of the band','Out of the band')

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

def splitCallsign(call):
    call = call.upper()
    m = re.match('(\w+)/(\w+)/(\w+)',call)
    if m:
        m2 = re.match('\d+',m.group(2))
        if m2:
            operator = m.group(1)
            portable = m.group(2)+'/'+m.group(3)
        else:
            operator = m.group(2)
            portable = m.group(1)
    else:
        m = re.match('(\w+)/(\w+)',call)
        if m:
            m2 = re.match('\d+',m.group(2))
            if m2:
                operator = m.group(1)
                portable = m.group(2)
            elif m.group(2).upper() == "QRP":
                operator = m.group(1)
                portable = m.group(2)
            elif len(m.group(2))>len(m.group(1)):
                operator = m.group(2)
                portable = m.group(1)
            else:
                operator = m.group(1)
                portable = m.group(2)
        else:
            operator = call.strip()
            portable = ''
            
    return (operator, portable)
    
def decodeHamlog(cols):

    errorfl = False
    errormsg = []
    
    if len(cols) < 15:
        errorfl = True
        errormsg = [ "Fatal:Too short columns." ]
        return {
            'error':True,
            'errormsg': errormsg
        }
    else:
        (operator, portable) = splitCallsign(cols[0])
        
        m = re.match('(\d+)/(\d+)/(\d+)',cols[1])
        if m:
            if len(m.group(1)) > 2:
                year = m.group(1)
            else:
                if int(m.group(1)) >= 65:
                    year = '19' + m.group(1)
                else:
                    year = '20' + m.group(1)
            month = m.group(2)
            day = m.group(3)
        else:
            errorfl = True
            errormsg.append("Wrong date format:{}".format(cols[1]))
            year = '1900'
            month = '01'
            day = '01'

        m = re.match('(\d\d):(\d\d)(\w)',cols[2])
        if m:
            hour = m.group(1)
            minute = m.group(2)
            fl = m.group(3).upper()
            if fl == 'U' or fl == 'Z':
                timezone = '+0000'
            else:
                timezone = '+0900'
        else:
            errorfl = True
            errormsg.append("Wrong time format:{}".format(cols[2]))
            hour = '00'
            minute = '00'
            timezone = '+0900'

        tstr = year + '/' + month + '/' + day + ' ' + hour + ':' + minute + ' ' + timezone
        try:
            atime = datetime.datetime.strptime(tstr,'%Y/%m/%d %H:%M %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
        except Exception as e:
            errorfl = True
            errormsg.append("Wrong time format:{}".format(operator+ ":"+tstr))
            atime = datetime.datetime.strptime("1900/1/1 0:0 +0000",'%Y/%m/%d %H:%M %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
        

        year = utime.year
        month = utime.month
        day = utime.day
        hour = utime.hour
        minute = utime.minute

        (band_air,band_sota,wlen) = freq_to_band(cols[5])

        qsl_sent = 0
        qsl_rcvd = 0
        qsl_via = ""
        qslflag = cols[9].upper() +'   '
        qslflag = qslflag[:3]
        
        if len(qslflag) == 3:
            if qslflag[0] == 'N':
                qsl_via = 'No Card'
            elif qslflag[0] == 'J':
                qsl_via = 'JARL (Bureau)'
            else:
                qsl_via = qslflag[0]

            if qslflag[1] != ' ':
                qsl_sent = 1
            if qslflag[2] != ' ':
                qsl_rcvd = 1
                
        return {
            'error':errorfl,
            'errormsg':" , ".join(errormsg),
            'callsign': cols[0],   # All
            'operator': operator,  # AirHam
            'portable': portable,  # AirHam
            'isotime': isotime,    # AirHam
            'year': year,          # SOTA,WWFF
            'month': month,        # SOTA,WWFF
            'day': day,            # SOTA,WWFF
            'hour': hour,          # SOTA,WWFF
            'minute': minute,      # SOTA,WWFF
            'timezone': timezone,  # AirHam
            'rst_sent': cols[3],   # All
            'rst_rcvd': cols[4],   # All
            'freq': cols[5],       # None
            'band': band_air,      # AirHam
            'band-sota': band_sota,# SOTA
            'band-wlen': wlen,     # WWFF
            'mode': cols[6],       # WWFF
            'mode-airham': mode_to_airhammode(cols[6],cols[5]), #AirHam
            'mode-sota': mode_to_SOTAmode(cols[6]), #SOTA
            'code': cols[7],   # None
            'gl': cols[8],     # None
            'qsl': qsl_via,    # AirHam
            'qsl_sent':qsl_sent, #AirHam
            'qsl_rcvd':qsl_rcvd, #AirHam
            'name': cols[10],  # None
            'qth': cols[11],   # None
            'rmks1': cols[12], # All
            'rmks2': cols[13]  # All
        }
    
def toAirHam(decoder, lcount, row, options):
    if lcount == 0:
        l= ["id","callsign","portable","qso_at","sent_rst",
            "received_rst","sent_qth","received_qth",
            "received_qra","frequency","mode","card",
            "remarks"]
        return l

    h = decoder(row)
    if h['error']:
        l = [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "HamLog format error at Line {}. : {}".format(lcount,h['errormsg'])
        ]
    else:
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
        m = re.match('.*?([a-zA-Z0-9]+FF-\d+).*',ref)
        if m:
            r['WWFF'] = m.group(1)
        m = re.match('.*?([a-zA-Z0-9]+/[a-zA-Z0-9]+-\d+).*',ref)
        if m:
            r['SOTA'] = m.group(1)
    return r

def toSOTA(decoder, actp, row, callsign, options):
    h = decoder(row)

    if options['myQTH']=='rmks1':
        myref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['myQTH']=='rmks2':
        myref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        myref = {'SOTA': options['Summit']}
        comment = ''

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

    if actp and myref['SOTA'] == '':
        return (date2,False,[])
    
    l = [
        "V2",
        callsign,
        myref['SOTA'],
        date,
        '{hour:02}:{minute:02}'.format(hour=h['hour'], minute=h['minute']),
        h['band-sota'],
        h['mode-sota'],
        h['callsign'],
        hisqth['SOTA'],
        ' '
    ]
    
    return (date2,hisqth['SOTA']!='',l)

def adif(key, value):
    adif_fields = [
        ('STATION_CALLSIGN','activator'),
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
        ('SOTA_REF', 'sotaref'),
        ('MY_SOTA_REF','mysotaref'),
        ('OPERATOR','operator'),
        ('PROGRAMID','programid'),
        ('ADIF_VER','adifver')
    ]
    for (field,k) in adif_fields:
        if key == k:
            f ='<' + field + ':' + str(len(value)) + '>' + value
            return f
    f ='<COMMENT:' + str(len(value)) + '>' + value
    return f
        
def toADIF(decoder, mode, row, options):
    h = decodeHamlog(row)

    if options['myQTH']=='rmks1':
        myref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['myQTH']=='rmks2':
        myref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        myref = {'SOTA': options['Summit']}
        comment = ''

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
    
    if mode == 'SOTA':
        activator = options['SOTAActivator']
        wwffref = ''
    else:
        activator = options['WWFFActivator']
        wwffref = options['WWFFRef']
        
    if mode == 'SOTA' and myref['SOTA']=='':
        return (date2,'',[])
    
    l = [
        adif('activator',activator),
        adif('callsign',h['callsign']),
        adif('date',date),
        adif('time',
             '{hour:02}{minute:02}'.format(
                 hour=h['hour'], minute=h['minute'])),
        adif('band-wlen',h['band-wlen']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
        ]
    
    if mode == 'SOTA':
        l += [ adif('mysotaref',myref['SOTA']) ]
        if  hisref['SOTA'] != '':
            l+= [adif('sotaref',hisref['SOTA'])]
    else:
        l += [ adif('mysig','WWFF'),
               adif('mysiginfo',options['WWFFRef'])]
        if hisref['WWFF'] != '':
            l+= [adif('sig','WWFF'),adif('siginfo',hisref['WWFF'])]

    l+= ['<EOR>']
    
    return (date2,wwffref,l)

def sendAirHamLog(fp, fname, decoder, options, inchar, outchar):

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=outchar, errors="backslashreplace")
    linecount = 0
    writer = csv.writer(sys.stdout,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    print('Content-Disposition: attachment;filename="%s"\n' % fname)
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        reader = csv.reader(f)
        try:
            for row in reader:
                if linecount > 100000:
                    break
                else:
                    if linecount == 0:
                        writer.writerow(toAirHam(decoder, linecount, row, options))
                        linecount += 1
                    writer.writerow(toAirHam(decoder, linecount, row, options))
                linecount += 1
        except Exception as e:
            print('Line:{} Error{}'.format(linecount, e))
                
def sendSOTA_A(fp, decoder, callsign, options, inchar, outchar):
    prefix = 'sota'
    prefix2 = 'sota-s2s-'
    fname = ''
    fname_adi = ''
    files = {}
    linecount = 0

    outstr = io.StringIO()
    writer = csv.writer(outstr,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    outstr_s2s = io.StringIO()
    writer_s2s = csv.writer(outstr_s2s,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)
    outstr_adif = io.StringIO()
    writer_adif = csv.writer(outstr_adif, delimiter=' ',
                             quoting=csv.QUOTE_MINIMAL)

    with io.TextIOWrapper(fp, encoding=inchar, errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (d2,ref,ladif) = toADIF(decoder, 'SOTA', row, options)
                (fn, s2s, lcsv) = toSOTA(decoder, True, row, callsign, options)

                if ladif:
                    if linecount==0:
                        fname_adi = d2
                        outstr_adif.write('ADIF Export from HAMLOG by JL1NIE\n')
                        outstr_adif.write(adif('programid','FCTH')+'\n')
                        outstr_adif.write(adif('adifver','3.0.6')+'\n')
                        outstr_adif.write('<EOH>\n')
                    writer_adif.writerow(ladif)

                if lcsv:
                    if linecount==0:
                        fname = fn

                    if fn == fname:
                        writer.writerow(lcsv)
                        if s2s:
                            writer_s2s.writerow(lcsv)
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
                        writer.writerow(lcsv)

                        outstr_s2s = io.StringIO()
                        writer_s2s = csv.writer(outstr_s2s,delimiter=',',
                                                quoting=csv.QUOTE_MINIMAL)
                        if s2s:
                            writer_s2s.writerow(lcsv)
                        fname = fn

                if ladif:
                    linecount += 1

        if fname_adi != '': 
            name = prefix + fname_adi + '.adi'
            files.update({name : outstr_adif.getvalue()})

        if fname != '':
            name = prefix + fname + '.csv'
            files.update({name : outstr.getvalue()})

            s2sbuff = outstr_s2s.getvalue()
            if len(s2sbuff) > 0:
                name2 = prefix2 + fname + '.csv'
                files.update({name2 : s2sbuff})

    return(files)

def sendSOTA_C(fp, decoder, callsign, options, inchar, outchar):
    prefix = 'sota'
    fname = ''
    files = {}
    linecount = 0

    outstr = io.StringIO()
    writer = csv.writer(outstr,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)

    outstr_nonsota = io.StringIO()
    writer_nonsota = csv.writer(outstr_nonsota,delimiter=',',
                              quoting=csv.QUOTE_MINIMAL)
    nonsota_fl = False
    
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (fn,his_summit,l) = toSOTA(decoder, False, row, callsign, options)
                if linecount == 0:
                    fname = fn
                    
                if his_summit:
                    writer.writerow(l)
                else:
                    writer_nonsota.writerow(l)
                    nonsota_fl = True

                linecount += 1

        name = prefix + fname + '.csv'
        files.update({name : outstr.getvalue()})
        if nonsota_fl :
            name = 'other'+ fname + '.csv'
            files.update({name : outstr_nonsota.getvalue()})
        
    return(files)

def sendWWFF(fp, decoder, options, inchar, outchar):
    files = {}
    outstr = io.StringIO()
    linecount = 0
    writer = csv.writer(outstr, delimiter=' ',
                        quoting=csv.QUOTE_MINIMAL)
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            else:
                (date,ref,l) = toADIF(decoder, 'WWFF', row, options)
                if linecount == 0:
                    act_call = options['WWFFActivator']
                    fname = act_call.replace('/','-') + '@' + ref + ' '+ date +'.adi'
                    outstr.write('ADIF Export from HAMLOG by JL1NIE\n')
                    outstr.write(adif('programid','FCTH')+'\n')
                    outstr.write(adif('adifver','3.0.6')+'\n')
                    outstr.write('<EOH>\n')
                writer.writerow(l)
                linecount += 1
        files.update({fname : outstr.getvalue()})

    return files
