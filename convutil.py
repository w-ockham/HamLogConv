#!/usr/bin/env python3
# coding: utf-8
import adif_io
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
    (1.8,1.9125,'1.9MHz','1.8MHz','160m'),
    (3.5,3.805,'3.8MHz','3.5MHz','80m'),
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
    (1200.0,1300.0,'1200MHz','1290MHz','23cm'),
    (2400.0,2450.0,'2400MHz','2.3GHz','13cm'),
    (5650.0,5850.0,'5600MHz','5.6GHz','6cm'),
    (10000.0,10250.0,'10.1GHz','10GHz','3cm'),
    (10450.0,10500.0,'10.4GHz','10GHz','3cm'),
    (351.0,351.38125,'デジタル簡易(351MHz)','',''),
    (421.0,454.19375,'特定小電力(422MHz)','',''),
    (26.968,27.144,'CB(27MHz)','',''),
    (142.0,147.0,'デジタル小電力コミュニティ(142/146MHz)','','')
]

JA_region_table = {
    'JA/NI':'0',
    'JA/NN':'0',
    'JA/TK':'1',
    'JA/KN':'1',
    'JA/CB':'1',
    'JA/ST':'1',
    'JA/IB':'1',
    'JA/TG':'1',
    'JA/GM':'1',
    'JA/YN':'1',
    'JA/SO':'2',
    'JA/GF':'2',
    'JA/AC':'2',
    'JA/ME':'2',
    'JA/KT':'3',
    'JA/SI':'3',
    'JA/NR':'3',
    'JA/OS':'3',
    'JA/WK':'3',
    'JA/HG':'3',
    'JA/OY':'4',
    'JA/SN':'4',
    'JA/YG':'4',
    'JA/TT':'4',
    'JA/HS':'4',
    'JA5/KA':'5',
    'JA5/TS':'5',
    'JA5/EH':'5',
    'JA5/KC':'5',
    'JA6/FO':'6',
    'JA6/SG':'6',
    'JA6/NS':'6',
    'JA6/KM':'6',
    'JA6/OT':'6',
    'JA6/MZ':'6',
    'JA6/KG':'6',
    'JA6/ON':'6',
    'JA/AM':'7',
    'JA/IT':'7',
    'JA/AT':'7',
    'JA/YM':'7',
    'JA/MG':'7',
    'JA/FS':'7',
    'JA8/SY':'8',
    'JA8/RM':'8',
    'JA8/KK':'8',
    'JA8/OH':'8',
    'JA8/SC':'8',
    'JA8/IS':'8',
    'JA8/NM':'8',
    'JA8/SB':'8',
    'JA8/TC':'8',
    'JA8/KR':'8',
    'JA8/HD':'8',
    'JA8/IR':'8',
    'JA8/HY':'8',
    'JA8/OM':'8',
    'JA/TY':'9',
    'JA/FI':'9',
    'JA/IK':'9'
}
    
def errMsg(val):
    return ('<font color="red"><b>' + str(val) + '</b></font>')
    
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
        
    raise Exception(freq_str)

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

def mode_to_ADIFmode(mode):
    mode_table = [
        ('DIGITALVOICE',['DV','FUSION','D-STAR','DMR'])]
    for smode,pat in mode_table:
        if mode.upper() in pat:
            return smode
    return mode.upper()

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
            errordate = ''
        else:
            errorfl = True
            errormsg.append("Err:Wrong date format:{}".format(cols[1]))
            year = '1900'
            month = '01'
            day = '01'
            errordate = errMsg(cols[1])
            
        m = re.match('(\d\d):(\d\d)(\w)',cols[2])
        if m:
            hour = m.group(1)
            minute = m.group(2)
            fl = m.group(3).upper()
            if fl == 'U' or fl == 'Z':
                timezone = '+0000'
            else:
                timezone = '+0900'
            errortime = ''
        else:
            errorfl = True
            errormsg.append("Err:Wrong time format:{}".format(cols[2]))
            hour = '00'
            minute = '00'
            timezone = '+0900'
            errortime = errMsg(cols[2])

        tstr = year + '/' + month + '/' + day + ' ' + hour + ':' + minute + ' ' + timezone
        try:
            atime = datetime.datetime.strptime(tstr,'%Y/%m/%d %H:%M %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
        except Exception as e:
            errorfl = True
            errormsg.append("Err:Wrong time format:{}".format(operator+ ":"+tstr))
            atime = datetime.datetime.strptime("1900/1/1 0:0 +0000",'%Y/%m/%d %H:%M %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
            [errordate ,errortime] = map(errMsg,[cols[1],cols[2]])
        
        year = utime.year
        month = utime.month
        day = utime.day
        hour = utime.hour
        minute = utime.minute

        try:
            (band_air,band_sota,wlen) = freq_to_band(cols[5])
            band_error = ''
        except Exception as e:
            band_error = errMsg(str(e))
            errormsg.append("Err:Frequency out of range:{}".format(e))
            (band_air,band_sota,wlen) = (band_error, band_error, band_error)
            
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
                qsl_via = qslflag

            if qslflag[1] != ' ':
                qsl_sent = 1
            if qslflag[2] != ' ':
                qsl_rcvd = 1
                
        return {
            'error':errorfl,
            'errormsg':" , ".join(errormsg),
            'date_error':errordate,
            'time_error':errortime,
            'band_error':band_error,
            
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
            'mode': mode_to_ADIFmode(cols[6]),       # WWFF
            'mode-airham': mode_to_airhammode(cols[6],cols[5]), #AirHam
            'mode-sota': mode_to_SOTAmode(cols[6]), #SOTA
            'code': cols[7],   # None
            'gl': cols[8],     # SOTA
            'qsl': qsl_via,    # AirHam
            'qsl_sent':qsl_sent, #AirHam
            'qsl_rcvd':qsl_rcvd, #AirHam
            'name': cols[10],  # None
            'qth': cols[11],   # SOTA
            'rmks1': cols[12], # All
            'rmks2': cols[13]  # All
        }

def decodeADIF(cols):
    qsos , header = adif_io.read_from_string(cols)
    qso = qsos[0]
    ( _, _, wlen ) = freq_to_band(qso['FREQ'])
    errorfl = False
    errormsg = ''
    if 'MY_SIG_INFO' in qso:
        my_sig = qso['MY_SIG_INFO']
    elif 'MY_SOTA_REF' in qso:
        my_sig = qso['MY_SOTA_REF']
    else:
        my_sig = 'UNKNOWN'
        errorfl = True
        errormsg = 'Not specified my reference.'

    if 'SIG_INFO' in qso:
        his_sig = qso['SIG_INFO']
    elif 'SOTA_REF' in qso:
        his_sig = qso['SOTA_REF']
    else:
        his_sig = 'UNKNOWN'
        errorfl = True
        errormsg = 'Not specified his reference.'

    return {
            'error':errorfl,
            'errormsg':errormsg,
            'date_error':'',
            'time_error':'',
            'band_error':'',
            
            'callsign': qso['CALL'] ,# All
            'year': int(qso['QSO_DATE'][0:4]),# SOTA,WWFF
            'month':int(qso['QSO_DATE'][4:6]),        # SOTA,WWFF
            'day': int(qso['QSO_DATE'][6:8]),            # SOTA,WWFF
            'hour': int(qso['TIME_ON'][0:2]),          # SOTA,WWFF
            'minute': int(qso['TIME_ON'][2:4]),      # SOTA,WWFF
            'rst_sent': qso['RST_SENT'],   # All
            'rst_rcvd': qso['RST_RCVD'],   # All
            'band-wlen': wlen,     # WWFF
            'mode': mode_to_ADIFmode(qso['MODE']),       # WWFF
            'rmks1': my_sig, # All
            'rmks2': his_sig# All
        }

def decodeHamLogIOS(cols):

    errorfl = False
    errormsg = []
    
    if len(cols) < 19:
        errorfl = True
        errormsg = [ "Fatal:Too short columns." ]
        return {
            'error':True,
            'errormsg': errormsg
        }
    else:
        (operator, portable) = splitCallsign(cols[3])
        errordate = ''
        errortime = ''
        try:
            atime = datetime.datetime.strptime(cols[0],'%Y-%m-%d %H:%M:%S %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
        except Exception as e:
            errorfl = True
            errormsg.append("Err:Wrong time format:{}".format(operator+ ":"+cols[0]))
            atime = datetime.datetime.strptime("1900/1/1 0:0 +0000",'%Y/%m/%d %H:%M %z')
            utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
            isotime = atime.isoformat()
            [errordate ,errortime] = map(errMsg, cols[0].split(' ')[0:2])
            


        year = utime.year
        month = utime.month
        day = utime.day
        hour = utime.hour
        minute = utime.minute
        timezone = '+0000'

        try:
            (band_air,band_sota,wlen) = freq_to_band(cols[2])
            band_error = ''
        except Exception as e:
            band_error = errMsg(str(e))
            errormsg.append("Err:Frequency out of range:{}".format(e))
            (band_air,band_sota,wlen) = (band_error,band_error,band_error)
            
        return {
            'error':errorfl,
            'errormsg':" , ".join(errormsg),
            'date_error':errordate,
            'time_error':errortime,
            'band_error':band_error,
            
            'callsign': cols[3],   # All
            'operator': operator,  # AirHam
            'portable': portable,  # AirHam
            'isotime': isotime,    # AirHam
            'year': year,          # SOTA,WWFF
            'month': month,        # SOTA,WWFF
            'day': day,            # SOTA,WWFF
            'hour': hour,          # SOTA,WWFF
            'minute': minute,      # SOTA,WWFF
            'timezone': timezone,  # AirHam
            'rst_sent': cols[5],   # All
            'rst_rcvd': cols[4],   # All
            'freq': cols[2],       # None
            'band': band_air,      # AirHam
            'band-sota': band_sota,# SOTA
            'band-wlen': wlen,     # WWFF
            'mode': cols[11],       # WWFF
            'mode-airham': mode_to_airhammode(cols[11],cols[2]), #AirHam
            'mode-sota': mode_to_SOTAmode(cols[11]), #SOTA
            'code': '',   # None
            'gl': cols[6],     # SOTA
            'qsl': cols[14],    # AirHam
            'qsl_sent':cols[15], #AirHam
            'qsl_rcvd':cols[16], #AirHam
            'name': cols[7],  # None
            'qth': cols[8],   # SOTA
            'rmks1': cols[8], # All
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
    r = {'SOTA':'', 'PORT':'', 'WWFF':[] ,'POTA':[],
         'LOC':'', 'LOC_org':'',
         'SAT':'','SAT_oscar':'','SAT_org':'','SAT_down':'',
         'ORG':'' }
    m = re.match(r'.*?(-?\d+(\.\d+)?[nsNS]?\s*,\s*\-?\d+(\.\d+)?[ewEW]?).*',
                 str)
    if m:
        r['LOC'] = '%QTH%' + m.group(1) + '% '
 
    l = re.split('[,\s]', str)
    for ref in l:
        m = re.match(r'.*?([a-zA-Z0-9]+FF-\d+).*',ref)
        if m:
            r['WWFF'].append(m.group(1).upper())
            continue

        m = re.match(r'.*?([a-zA-Z0-9]+-\d\d\d\d).*',ref)
        if m:
            r['POTA'].append(m.group(1).upper())
            continue

        m = re.match(r'.*?(([a-zA-Z0-9]+/[a-zA-Z0-9]+)-\d+).*',ref)
        if m:
            r['SOTA'] = m.group(1).upper()
            p = m.group(2).upper()
            if p in JA_region_table:
                r['PORT'] = JA_region_table[p]
            else:
                r['PORT'] = 'P'
            continue

        m = re.match(r'.*?([a-zA-Z]{2}\d{2}[a-zA-Z]{2}).*',ref)
        if m:
            r['LOC'] = '%QRA%' + m.group(1) + '% '
            r['LOC_org'] = m.group(1)
            continue
        
        m = re.match(r'.*?(([a-zA-Z]+-\d+)/([a-zA-Z]+/(\w+))).*',ref)
        if m:
            r['SAT'] = '%SAT%' + m.group(2).upper() + '%,'+ m.group(3)
            r['SAT_oscar'] = m.group(2).upper()
            r['SAT_org'] = m.group(1)
            r['SAT_down'] = m.group(4)
            continue
        
        r['ORG'] += ref + ' '
    r['ORG'] = r['ORG'].strip()
    return r

def toSOTA(decoder, lcount, actp, row, callsign, options):
    h = decoder(row)
    if h['error']:
        l = [
            "HamLog format error at Line {}. : {}".format(lcount,h['errormsg']),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ]
        return ("000000", False, l)
    else:
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
            if actp:
                comment = hisqth
            else:
                comment = get_ref(h['rmks2'])
        elif options['QTH']=='rmks2':
            hisqth = get_ref(h['rmks2'])
            if actp:
                comment = hisqth
            else:
                comment = get_ref(h['rmks1'])
        else:
            hisqth = {'SOTA':'', 'LOC': ' '}
            comment = hisqth

        date = '{day:02}/{month:02}/{year:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])

        date2 = '{year:02}{month:02}{day:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])

        if actp and myref['SOTA'] == '':
            return (date2, True, [])
    
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
            comment['LOC']+' '
        ]
        return (date2,hisqth['SOTA']!='',l)

def toSOTA_Both(decoder, lcount, row, callsign, options):
    h = decoder(row)
    if h['error']:
        l = [
            "HamLog format error at Line {}. : {}".format(lcount,h['errormsg']),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ]
        return ("000000", False, l)
    else:
        date = '{day:02}/{month:02}/{year:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])

        date2 = '{year:02}{month:02}{day:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])

        if options['myQTH']=='rmks1':
            myref = get_ref(h['rmks1'])
        else:
            myref = get_ref(h['rmks2'])

        if myref['SOTA'] != '':
            date2 = date2 + '-' + re.sub('.+/', '', myref['SOTA'])
            if options['Portable'] == 'fromsummit':
                callsign = callsign.upper() + '/' + myref['PORT']
            elif options['Portable'] == 'portable':
                callsign = callsign.upper() + '/P'
                
        if options['hisQTH']=='rmks1':
            hisqth = get_ref(h['rmks1'])
        else:
            hisqth = get_ref(h['rmks2'])

        if hisqth['SOTA'] == '' and options['hisQTHopt']:
            hisqth = get_ref(h['qth'])

        if options['Note']=='rmks1':
            comment = get_ref(h['rmks1'])
        else:
            comment = get_ref(h['rmks2'])

        gl = get_ref(h['gl'])
        
    
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
            gl['LOC'] + comment['SAT'] + ' '
        ]

        if myref['SOTA'] == '':
            if hisqth['SOTA'] == '':
                state = 0 #Other
            else:
                state = 1 #Chaser
        else:
            state = 2 #Activator
            
        return (date2, state, l)

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
        
def toADIF(decoder, lcount, mode, row, options):
    h = decoder(row)
    if options['myQTH']=='rmks1':
        myref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['myQTH']=='rmks2':
        myref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        myref = {'SOTA': options['Summit'], 'POTA':options['Park']}
        comment = ''

    if options['QTH']=='rmks1':
        hisref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        hisref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        hisref = {'SOTA':'','WWFF':'','POTA':''}
        comment = ''
        
    if h['date_error']:
        date = h['date_error']
    else:
        date = '{year:02}{month:02}{day:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])
    
    date2 = '{year:02}-{month:02}-{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])

    if h['time_error']:
        time = h['time_error']
    else:
        time = '{hour:02}{minute:02}'.format(
            hour=h['hour'], minute=h['minute'])

    if mode == 'SOTA':
        activator = options['SOTAActivator']
        (operator,_) = splitCallsign(activator)
        wwffref = ''
    elif mode == 'POTA':
        activator = options['POTAActivator']
        operator = options['POTAOperator']
        wwffref = myref['POTA']
    else:
        activator = options['WWFFActivator']
        operator = options['WWFFOperator']
        wwffref = options['WWFFRef']
        
    if mode == 'SOTA' and myref['SOTA']=='':
        return (date2,'',[],[],False)
    elif mode == 'POTA' and myref['POTA']=='':
        return (date2,'',[],[],False)

    if h['error'] or (mode == 'POTA' and h['band_error']):
        l = [h['errormsg']]
        l2 = []
        errorfl = True
    else:
        l = []
        l2 = []
        errorfl = False
          
    l += [
        adif('activator',activator),
        adif('operator',operator),
        adif('callsign',h['callsign']),
        adif('date',date),
        adif('time',time),
        adif('band-wlen',h['band-wlen']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
    ]
    if mode == 'POTA':
        l2 += [
            h['callsign'],
            date,
            time,
            h['band-wlen'],
            h['mode'],
            h['rst_sent'],
            h['rst_rcvd'],
            hisref['POTA'],
            myref['POTA'],
            activator,
            operator
        ]
            
    if mode == 'SOTA':
        l += [ adif('mysotaref',myref['SOTA']) ]
        if  hisref['SOTA'] != '':
            l+= [adif('sotaref',hisref['SOTA'])]
    elif mode == 'POTA':
        l += [ adif('mysig','POTA'),
               adif('mysiginfo',myref['POTA'])]
        if hisref['POTA'] != '':
            l+= [adif('sig','POTA'),adif('siginfo',hisref['POTA'])]
    else:
        l += [ adif('mysig','WWFF'),
               adif('mysiginfo',options['WWFFRef'])]
        if hisref['WWFF'] != '':
            l+= [adif('sig','WWFF'),adif('siginfo',hisref['WWFF'])]
            
    l+= ['<EOR>']
    
    return (date2, wwffref, l, l2, errorfl)

def toADIF2(decoder, row, options):

    h = decoder(row)

    if options['myQTH']=='rmks1':
        myref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['myQTH']=='rmks2':
        myref = get_ref(h['rmks2'])
        comment = h['rmks1']
    else:
        myref = get_ref(options['Park'])
        comment = ''
        
    if myref['SOTA'] != '':
        myref['SOTA'] = [myref['SOTA']]
    else:
        myref['SOTA'] = []
        
    if options['QTH']=='rmks1':
        hisref = get_ref(h['rmks1'])
        comment = h['rmks2']
    elif options['QTH']=='rmks2':
        hisref = get_ref(h['rmks2'])
        comment = h['rmks1']
    elif options['QTH']=='qth':
        hisref = get_ref(h['qth'])
        comment = h['rmks2']
    else:
        hisref = {'SOTA':'', 'POTA':[],'WWFF':[]}
        comment = ''

    if hisref['SOTA'] != '':
        hisref['SOTA'] = [hisref['SOTA']]
    else:
        hisref['SOTA'] = []

    if h['date_error']:
        date = h['date_error']
    else:
        date = '{year:02}{month:02}{day:02}'.format(
            day=h['day'], month=h['month'], year=h['year'])
    
    date2 = '{year:02}-{month:02}-{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])

    if h['time_error']:
        time = h['time_error']
    else:
        time = '{hour:02}{minute:02}'.format(
            hour=h['hour'], minute=h['minute'])

    activator = options['POTAActivator']
    operator = options['POTAOperator']

    if h['error'] or h['band_error']:
        qso = [h['errormsg']]
        errorfl = True
    else:
        qso = []
        errorfl = False

    if options['OmitPortable'] == 'checked' and myref['POTA']:
        (potacall,_) = splitCallsign(h['callsign'])
    else:
        potacall = h['callsign']
        
    qsopota = qso + [
        adif('activator',activator),
        adif('operator',operator),
        adif('callsign',potacall),
        adif('date',date),
        adif('time',time),
        adif('band-wlen',h['band-wlen']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
    ]

    qso += [
        adif('activator',activator),
        adif('operator',operator),
        adif('callsign',h['callsign']),
        adif('date',date),
        adif('time',time),
        adif('band-wlen',h['band-wlen']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
    ]
    
    log = {}

    for my in myref['SOTA']:
       log[my] = []
       if hisref['SOTA']:
           for his in hisref['SOTA']:
               log[my] += qso + [ adif('mysotaref',my),
                                  adif('sotaref',his),'<EOR>\n']
       else:
           log[my] += qso + [ adif('mysotaref',my),'<EOR>\n']

    for my in myref['POTA']:
        log[my] = []
        if hisref['POTA']:
            for his in hisref['POTA']:
                log[my] += qsopota + [
                    adif('mysig','POTA'),
                    adif('mysiginfo',my),
                    adif('sig','POTA'),
                    adif('siginfo',his),'<EOR>\n']
        else:
            log[my] += qsopota + [
                adif('mysig','POTA'),
                adif('mysiginfo',my),'<EOR>\n']

    for my in myref['WWFF']:
        log[my] = []
        if hisref['WWFF']:
            for his in hisref['WWFF']:
                log[my] += qso + [
                    adif('mysig','WWFF'),
                    adif('mysiginfo',my),
                    adif('sig','WWFF'),
                    adif('siginfo',his),'<EOR>\n']
        else:
            log[my] += qso + [
                adif('mysig','WWFF'),
                adif('mysiginfo',my),'<EOR>\n']

    make_str = lambda x : '/'.join(x['SOTA']+ x['WWFF']+ x['POTA'])
    hisstr = make_str(hisref)
    mystr = make_str(myref) 
    ldisp = [
            potacall,
            date,
            time,
            h['band-wlen'],
            h['mode'],
            h['rst_sent'],
            h['rst_rcvd'],
            hisstr,
            mystr,
            activator,
            operator
        ]

    return (date2, ldisp, log, errorfl)

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
                
def sendSOTA_Both(fp, decoder, callsign, options, inchar, outchar):
    prefix = 'sotaActivation-'
    prefix2 = 'sotaChaser-'
    prefix3 = 'other-'
    fname_act = ''
    fname_chs = ''
    files = {}
    linecount = 0

    outstr_act = io.StringIO()
    writer_act = csv.writer(outstr_act,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

    outstr_chs = io.StringIO()
    writer_chs = csv.writer(outstr_chs,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

    outstr_other = io.StringIO()
    writer_other = csv.writer(outstr_other,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

    with io.TextIOWrapper(fp, encoding=inchar, errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            elif row:
                (fn, state, lcsv) = toSOTA_Both(decoder, linecount, row, callsign, options)
                if linecount==0:
                    fname_act = fn
                    fname_chs = fn
                        
                if fn == fname_act:
                    if state == 0:
                        writer_other.writerow(lcsv)
                    elif state == 1:
                        writer_chs.writerow(lcsv)
                    else:
                        writer_act.writerow(lcsv)
                else:
                    buff = outstr_act.getvalue()
                    if len(buff) > 0:
                        name = prefix + fname_act + '.csv'
                        files.update({name : buff})
                        
                    outstr_act = io.StringIO()
                    writer_act = csv.writer(outstr_act,delimiter=',',
                                            quoting=csv.QUOTE_MINIMAL)
                    if state == 0:
                        writer_other.writerow(lcsv)
                    elif state == 1:
                        writer_chs.writerow(lcsv)
                    else:
                        writer_act.writerow(lcsv)

                    fname_act = fn

            linecount += 1

        buff = outstr_act.getvalue()
        if len(buff) > 0:
            name = prefix + fname_act + '.csv'
            files.update({name : buff})

        buff = outstr_chs.getvalue()
        if len(buff) > 0:
            name = prefix2 + fname_chs + '.csv'
            files.update({name : buff})

        buff = outstr_other.getvalue()
        if len(buff) > 0:
            name = prefix3 + fname_chs + '.csv'
            files.update({name : buff})

    return(files)

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
            elif row:
                (d2,ref,ladif,_,_) = toADIF(decoder, linecount, 'SOTA', row, options)
                (fn, s2s, lcsv) = toSOTA(decoder, linecount, True, row, callsign, options)

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
            elif row:
                (fn,his_summit,l) = toSOTA(decoder, linecount, False, row, callsign, options)
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
                (date,ref,l,_,_) = toADIF(decoder, linecount, 'WWFF', row, options)
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

def sendADIF(fp, options, inchar, outchar):
    files = {}
    res = {'status':'OK','logtext':[]}
    header = 'ADIF Export from HAMLOG by JL1NIE\n'+ adif('programid','FCTH')+ '\n' + adif('adifver','3.0.6')+'\n' + '<EOH>\n'
    
    act_call = options['POTAActivator']
    (operator,portable) = splitCallsign(act_call)

    if not options['POTAOperator']:
        options['POTAOperator'] = operator

    lines = []
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            lines += [row]

    decoder = None
    linecount = 0
    isADIF = False
    
    if 'ADIF_VER' in lines[0][0].upper():
        r = lines
        lines = []
        isADIF = True
        isbody = False
        options['myQTH'] = 'rmks1'
        options['QTH'] = 'rmks2'
        for l in r:
            lstr = ','.join(l)
            if isbody:
                lines.append(lstr)
            elif 'EOH' in lstr:
                isbody = True
    
    for row in lines:
        if linecount > 100000:
            break

        if not decoder:
            if 'TimeOn' in row:
                decoder = decodeHamLogIOS
                continue
            elif isADIF:
                decoder = decodeADIF
            else:
                decoder = decodeHamlog
                    
        (date, ldisp, log, errorfl) = toADIF2(decoder, row, options)

        if errorfl:
            res['status'] = 'NG'

        if ldisp:
            res['logtext'].append(ldisp)

        for ref in log.keys():
            fn = act_call.replace('/','-') + '@' + ref.replace('/','-') + '-' + date +'.adi'
            if files.get(fn) == None:
                files[fn] = header

            if log[ref]:
                files[fn] += ''.join(log[ref])

        linecount += 1

    return files,res

def sendPOTA(fp, options, inchar, outchar):
    files = {}
    res = {'status':'OK','logtext':[]}
    outstr = io.StringIO()
    linecount = 0
    fname = ''
    writer = csv.writer(outstr, delimiter=' ',
                        quoting=csv.QUOTE_MINIMAL)
    header = 'ADIF Export from HAMLOG by JL1NIE\n' + adif('programid','FCTH')+ '\n' + adif('adifver','3.0.6')+'\n' + '<EOH>\n'
    
    act_call = options['POTAActivator']
    (operator,portable) = splitCallsign(act_call)
    if not options['POTAOperator']:
        options['POTAOperator'] = operator

    decoder = None
        
    with io.TextIOWrapper(fp, encoding=inchar,errors="backslashreplace") as f:
        reader = csv.reader(f)
        for row in reader:
            if linecount > 100000:
                break
            if not decoder:
                if 'TimeOn' in row:
                    decoder = decodeHamLogIOS
                    continue
                else:
                    decoder = decodeHamlog
                    
            (date,ref,l,l2,errorfl) = toADIF(decoder, linecount, 'POTA', row, options)
            if errorfl:
                res['status'] = 'NG'
                
            fn = act_call.replace('/','-') + '@' + ref + '-' + date +'.adi'
            if l:
                if linecount==0:
                    fname = fn
                    
                if fn == fname:
                    writer.writerow(l)
                else:
                    if fname in files:
                        newstr = files[fname] + outstr.getvalue()
                    else:
                        newstr = header + outstr.getvalue()

                    files.update({fname : newstr })
                    outstr = io.StringIO()
                    writer = csv.writer(outstr,delimiter=' ',
                                        quoting=csv.QUOTE_MINIMAL)
                    fname = fn
                    writer.writerow(l)
            if l2:
                res['logtext'].append(l2)
            linecount += 1

        if fname != '':
            if fname in files:
                newstr = files[fname] + outstr.getvalue()
            else:
                newstr = header + outstr.getvalue()
            files.update({fname : newstr })
            
    return files,res
