#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import csv
import datetime
import io
import json
import re
import sys
from convutil import (
    writeZIP,
    freq_to_band,
    band_to_freq,
    splitCallsign,
    mode_to_airhammode,
    mode_to_SOTAmode,
    adif
)


debug = False
#debug = True

keyword_table = {
    'mycall':1,
    'operator':1,
    'qslmsg':-1,
    'mywwff':1,
    'mysota':1,
    'nickname':1,
    'date':1,
    'day':1,
}

def keyword(key):
    try:
        arg = keyword_table[key.lower()]
    except Exception as e:
        return None
    return((key.lower(),arg))

mode_table = {
    'cw':'rst',
    'ssb':'rs',
    'fm':'rs',
    'am':'rs',
    'rtty':'rst',
    'rtty':'rst',
    'rty':'rst',
    'psk':'rst',
    'psk31':'rst',
    'data':'snr',
    'jt9':'snr',
    'jt65':'snr',
    'ft8':'snr',
    'ft4':'snr',
    'dv':'rs',
    'fusion':'rs',
    'dstar':'rs',
    'd-star':'rs',
    'dmr':'rs',
    'c4fm':'rs'
}

def modes(key):
    try:
        arg = mode_table[key.lower()]
    except Exception as e:
        return None
    return(key.upper())

def modes_sig(key):
    try:
        arg = mode_table[key.lower()]
    except Exception as e:
        return None
    return(arg)
    
def tokenizer(line):
    res = []
    pos = []
    words = re.split('\s',line)
    for word in words:
        w = word.upper()

        if len(w) == 0:
            continue
        if w[0] == '#':
            break
        m = re.match('(\d+)-(\d+)-(\d+)$',w)
        if m:
            res.append(('date',(m.group(1),m.group(2),m.group(3)),w))
            continue
        m = re.match('(\d+)-(\d+)$',w)
        if m:
            res.append(('date2',(m.group(1),m.group(2)),w))
            continue
        m = re.match('(\d+)/(\d+)/(\d+)$',w)
        if m:
            res.append(('date',(m.group(1),m.group(2),m.group(3)),w))
            continue
        m = re.match('(\d+)/(\d+)$',w)
        if m:
            res.append(('date2',(m.group(1),m.group(2)),w))
            continue
        m = re.match('\d+\.\d+$',w)
        if m:
            res.append(('freq',freq_to_band(w),w))
            continue
        m = re.match('-\d+$',w)
        if m:
            res.append(('snr',w,w))
            continue
        bd = band_to_freq(w)
        if bd:
            res.append(('band',bd,word))
            continue
        m = re.match('\w+FF-\d+$',w)
        if m:
            res.append(('wwffref',w,word))
            continue
        m = re.match('\w+/\w+-\d+$',w)
        if m:
            res.append(('sotaref',w,word))
            continue
        kw = keyword(w)
        if kw:
            if w == 'QSLMSG':
                w2 = re.sub('qslmsg\s+','',line)
                res.append(('kw',kw,w2))
                break
            else:
                res.append(('kw',kw,word))
                continue
        md = modes(w)
        if md:
            res.append(('md',md,word))
            continue
        m = re.match('\d+$',w)
        if m:
            res.append(('dec',len(w),w))
            continue
        m = re.match('[\w|/]+$',w)
        if m:
            res.append(('id',w.upper(),word))
        else:
            res.append(('unknown',w.upper(),word))
    return(res)

def compileFLE(input_text,conv_mode):
    res = []
    (NORM,FREQ,RSTS,RSTR)=(1,2,3,4)
    env = {
        'mycall':'JL1NIE',
        'operator':'JL1NIE',
        'qslmsg':'',
        'mywwff':'',
        'mysota':'',
        'nickname':'',
        'year':2000,
        'month':1,
        'day':1,
        'c_year':2000,
        'c_month':1,
        'c_day':1,
        'c_hour':0,
        'c_min':0,
        'c_mode':'cw',
        'c_band':'20m',
        'c_freq':'14.062',
        'c_call':'',
        'c_his_wwff':'',
        'c_his_sota':'',
        'c_r_s':5,
        'c_s_s':9,
        'c_t_s':9,
        'c_r_r':5,
        'c_s_r':9,
        'c_t_r':9,
        'errno':[]
    }
    
    lines = input_text.splitlines()
    lc = 0
    qsoc = 0
    sotafl = False
    wwfffl = False
    for l in lines:
        env['c_r_s']=5
        env['c_s_s']=9
        env['c_t_s']=9
        env['c_r_r']=5
        env['c_s_r']=9
        env['c_t_r']=9
        env['c_call']=''
        env['c_snr_s']='-10'
        env['c_snr_r']='-10'
        env['c_his_wwff']=''
        env['c_his_sota']=''
        tl = tokenizer(l)
        if not tl:
            lc+=1
            continue
        pos = 0
        ml = len(tl) -1
        (t,p1,p2) = tl[pos]
        if t == 'kw':
            (key, l) = p1
            if key == 'day':
                if pos < ml:
                    (id, inc, w) = tl[pos+1]
                    d = datetime.datetime(env['c_year'],env['c_month'],env['c_day'])
                    delta = datetime.timedelta(days=0)
                    if w == '+':
                        delta = datetime.timedelta(days=1)
                    elif w == '++':
                        delta = datetime.timedelta(days=2)
                    else:
                        env['errno'].append((lc,pos+1,'Unknown operand'))
                        lc += 1
                        continue
                    d = d + delta
                    env['c_year'] = d.year
                    env['c_day'] = d.day
                    env['c_month'] = d.month
                else:
                    env['errno'].append((lc,pos+1,'Missing operand +/++'))
                lc += 1
                continue
            if key == 'mycall':
                if pos < ml:
                    (id, call, w) = tl[pos+1]
                    if id =='id':
                        env['mycall'] = call
                    else:
                        env['errno'].append((lc,pos+1,'Invalid callsign'))
                else:
                    env['errno'].append((lc,pos,'Missing operand'))

                lc += 1                    
                continue
            if key == 'operator':
                if pos < ml:
                    (id, op, w) = tl[pos+1]
                    if id =='id':
                        env['operator'] = op
                    else:
                        env['errno'].append((lc,pos+1,'Invalid operator'))
                else:
                    env['errno'].append((lc,pos,'Missing operand'))
                lc += 1
                continue
            if key == 'mywwff':
                if pos < ml:
                    (id, ref, w) = tl[pos+1]
                    if id =='wwffref':
                        env['mywwff'] = ref
                        wwfffl = True
                    else:
                        env['errno'].append((lc,pos+1,'Invalid WWFF ref#'))
                else:
                    env['errno'].append((lc,pos,'Missing WWFF ref#'))
                lc += 1
                continue
            if key == 'mysota':
                if pos < ml:
                    (id, ref, w) = tl[pos+1]
                    if id =='sotaref':
                        env['mysota'] = ref
                        sotafl = True
                    else:
                        env['errno'].append((lc,pos+1,'Invalid SOTA ref#'))
                else:
                    env['errno'].append((lc,pos,'mywwff','Missing WWFF ref#'))
                lc += 1
                continue
            if key == 'nickname':
                if pos < ml:
                    (_, _, w) = tl[pos+1]
                    env['nickname'] = w
                else:
                    env['errno'].append((lc,pos,'Missing operand'))
                lc += 1
                continue
            if key == 'qslmsg':
                p2 = re.sub('\$mywwff',env['mywwff'],p2)
                p2 = re.sub('\$mysota',env['mysota'],p2)
                env['qslmsg'] = p2
                lc += 1
                continue
            if key == 'date':
                if pos < ml:
                    (d, dp, w) = tl[pos+1]
                    if d =='date':
                        (y,m,d) = dp
                        env['c_year'] = int(y)
                        env['year'] = int(y)
                        env['c_month'] = int(m)
                        env['month'] = int(m)
                        env['c_day'] = int(d)
                        env['day'] = int(d)
                    elif d =='date2':
                        (m,d) = dp
                        env['c_month'] = int(m)
                        env['month'] = int(m)
                        env['c_day'] = int(d)
                        env['day'] = int(d)
                    else:
                        env['errno'].append((lc,pos+1,'Wrong date format.'))
                else:
                    env['errno'].append((lc,pos,'Missing operand'))
                lc += 1
                continue
        else:
            length = len(tl)
            state = NORM
            while pos < length:
                (t,p1,p2) = tl[pos]
                if state == NORM:
                    if t == 'md':
                        env['c_mode'] = p1
                        state = NORM
                        pos += 1
                        continue
                    if t == 'band':
                        env['c_band'] =p2
                        state = FREQ
                        pos += 1
                        continue
                    if t == 'dec':
                        if p1 == 1:
                            env['c_min'] = int(env['c_min']//10)*10 + int(p2)
                        elif p1 ==2:
                            env['c_min'] = int(p2) % 60
                        elif p1 == 3:
                            h = int(p2) // 100
                            m = int(p2) % 60
                            env['c_hour'] = int(env['c_hour']//10)*10 + h
                            env['c_min'] = m
                        elif p1 == 4:
                            h = int(p2) // 100
                            m = int(p2) %100 % 60
                            env['c_hour'] = h
                            env['c_min'] = m
                        else:
                            env['errno'].append((lc,pos,'Wrong time format.'))
                        pos+=1
                        state = NORM
                        continue
                    if t == 'freq':
                        env['c_freq'] = p2
                        (f,b) =freq_to_band(p2)
                        if f == 'Out of the band':
                            env['errno'].append((lc,pos,'Unknown band.'))
                        env['c_band'] = b
                        pos+=1
                        state = NORM
                        continue
                    if t == 'wwffref':
                        env['c_his_wwff'] = p1
                        pos+=1
                        state = NORM
                        continue
                    if t == 'sotaref':
                        env['c_his_sota'] = p1
                        pos+=1
                        state = NORM
                        continue
                    if t == 'id':
                        prev = env['c_call'] 
                        if  prev != '':
                            env['errno'].append((lc,pos,'Dupe call?:'+prev+','+p1))
                        env['c_call'] = p1
                        pos+=1
                        qsoc+=1
                        state = RSTS
                        continue
                    if t == 'unknown':
                        env['errno'].append((lc,pos,'Unknown literal:'+p1))
                    pos+=1
                    state = NORM
                elif state == FREQ:
                    if t == 'freq':
                        env['c_freq'] = p2
                        (f,b) = freq_to_band(p2)
                        if f == 'Out of the band':
                            env['errno'].append((lc,pos,'Out of the band.'))
                        env['c_band'] = b
                        pos+=1
                        state = NORM
                        continue
                    else:
                        state = NORM
                        continue
                elif state == RSTS:
                    if t == 'dec':
                        if p1 == 1:
                            env['c_s_s'] = int(p2)
                            pos += 1
                            state = RSTR
                            continue
                        elif p1 == 2:
                            env['c_r_s'] = int(p2)//10
                            env['c_s_s'] = int(p2)%10
                            pos += 1
                            state = RSTR
                            continue
                        elif p1 == 3:
                            env['c_r_s'] = int(p2)//100
                            env['c_s_s'] = (int(p2)%100)//10
                            env['c_t_s'] = int(p2)%10
                            pos += 1
                            state = RSTR
                            continue
                    elif t == 'snr':
                        env['c_snr_s'] = p1
                        pos += 1
                        state = RSTR
                        continue
                    else:
                        state = NORM
                        continue
                elif state == RSTR:
                    if t == 'dec':
                        if p1 == 1:
                            env['c_s_r'] = int(p2)
                            pos += 1
                            state = NORM
                            continue
                        elif p1 == 2:
                            env['c_r_r'] = int(p2)//10
                            env['c_s_r'] = int(p2)%10
                            pos += 1
                            state = NORM
                            continue
                        elif p1 == 3:
                            env['c_r_r'] = int(p2)//100
                            env['c_s_r'] = (int(p2)%100)//10
                            env['c_t_r'] = int(p2)%10
                            pos += 1
                            state = NORM
                            continue
                    elif t == 'snr':
                        env['c_snr_r'] = p1
                        pos += 1
                        state = NORM
                        continue
                    else:
                        state = NORM
                        continue
            lc+=1
        if env['c_call'] != '':
            if conv_mode : # GenerateLog
                rt = modes_sig(env['c_mode'])
                if rt == 'rst':
                    rsts = '{}{}{}'.format(env['c_r_s'],env['c_s_s'],env['c_t_s'])
                    rstr = '{}{}{}'.format(env['c_r_r'],env['c_s_r'],env['c_t_r'])
                elif rt == 'rs':
                    rsts = '{}{}'.format(env['c_r_s'],env['c_s_s'])
                    rstr = '{}{}'.format(env['c_r_r'],env['c_s_r'])
                elif rt == 'snr':
                    rsts = env['c_snr_s']
                    rstr = env['c_snr_r']

                qso = {
                    'mycall': env['mycall'],
                    'year':env['c_year'],
                    'month':env['c_month'],
                    'day':env['c_day'],
                    'hour':env['c_hour'],
                    'min':env['c_min'],
                    'callsign':env['c_call'],
                    'band':env['c_band'],
                    'mode':env['c_mode'],
                    'rst_sent': rsts,
                    'rst_rcvd': rstr,
                    'mysota':env['mysota'],
                    'hissota':env['c_his_sota'],
                    'mywwff':env['mywwff'],
                    'hiswwff':env['c_his_wwff'],
                    'operator':env['operator']
                }
            else: #Online
                mycall = env['mycall']
                call = env['c_call']
                date = '{y:02}-{m:02}-{d:02}'.format(y=env['c_year'],m=env['c_month'],d=env['c_day'])
                time = '{h:02}:{m:02}'.format(h=env['c_hour'],m=env['c_min'])
                band = env['c_band']
                mode = env['c_mode']
                rt = modes_sig(mode)
                if rt == 'rst':
                    rsts = '{}{}{}'.format(env['c_r_s'],env['c_s_s'],env['c_t_s'])
                    rstr = '{}{}{}'.format(env['c_r_r'],env['c_s_r'],env['c_t_r'])
                elif rt == 'rs':
                    rsts = '{}{}'.format(env['c_r_s'],env['c_s_s'])
                    rstr = '{}{}'.format(env['c_r_r'],env['c_s_r'])
                elif rt == 'snr':
                    rsts = env['c_snr_s']
                    rstr = env['c_snr_r']
                    
                mysota = env['mysota']
                hissota = env['c_his_sota']
                mywwff = env['mywwff']
                hiswwff = env['c_his_wwff']
                operator = env['operator']
                qso = [ str(qsoc), mycall, date, time, call, band, mode, rsts, rstr, mysota, hissota,mywwff, hiswwff ,operator]
            res.append(qso)

    if conv_mode:
        if len(env['errno'])>0:
            print("Content-Type:text/html\n\n")
            print("<h4><font color=\"#ff0000\">Interpretation Error!</font></h4>")
            print("<p><input type=\"button\" value=\"back\" onclick=\"history.back()\"></p>")
            return("")
        
        now  = datetime.datetime.now()
        fname = "fle-" + now.strftime("%Y-%m-%d-%H-%M")
        aday = '{}{:02}{:02}'.format(env['year'],env['month'],env['day'])
        logname= aday + '@' + env['mysota'].replace('/','-')+env['mywwff']
        files = {
            "fle-" + logname + ".txt" :input_text,
            "hamlog-" + logname + ".csv" : sendHamlog_FLE(res,'hisref',env),
            "airham-" + logname + ".csv" : sendAirHam_FLE(res,env)
        }
        
        if sotafl and wwfffl:
            files = sendSOTA_FLE(files,res)
            files = sendWWFF_FLE(files, res, env['mycall'])
            writeZIP(files,fname+".zip")
        elif sotafl:
            files = sendSOTA_FLE(files,res)
            writeZIP(files,fname+".zip")
        elif wwfffl:
            files = sendWWFF_FLE(files, res, env['mycall'])
            writeZIP(files,fname+".zip")
    else:
        if len(env['errno'])>0:
            status ='ERR'
            logtype = 'NONE'
            errors = env['errno']
            lines = input_text.splitlines()
            lc = 0
            res = []
            for l in lines:
                e = findErrors(lc,errors)
                if e:
                    res.append([str(lc),e, l])
                else:
                    res.append([str(lc),"", l])
                lc += 1
        else:
            status = 'OK'
            if sotafl and wwfffl:
                logtype = 'BOTH'
            elif sotafl:
                logtype = 'SOTA'
            elif wwfffl:
                logtype = 'WWFF'
            else:
                logtype = 'NONE'

        logtext = res
        errmsg = env['errno']
        
        res = {'status': status,
               'logtype': logtype,
               'mycall':env['mycall'],
               'operator':env['operator'],
               'mysota':env['mysota'],
               'mywwff':env['mywwff'],
               'qslmsg':env['qslmsg'],
               'logtext': logtext,
        }
        return (res)
    
def findErrors(lc,err):
    for e in err:
        (l,c,msg) = e
        if lc == l:
            return msg
    return None

def toSOTAFLE(h):
    date = '{day:02}/{month:02}/{year:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])

    date2 = '{year:02}{month:02}{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])

    f =band_to_freq(h['band'])

    l = [
        "V2",
        h['mycall'],
        h['mysota'],
        date,
        '{hour:02}:{minute:02}'.format(hour=h['hour'], minute=h['min']),
        f,
        mode_to_SOTAmode(h['mode']),
        h['callsign'],
        h['hissota'],
        ''
    ]
    return (date2,h['hissota']!='',l)

def sendSOTA_FLE(files, loginput):
    prefix = 'sota'
    prefix2 = 'sota-s2s-'
    fname = ''
    linecount = 0

    outstr = io.StringIO()
    writer = csv.writer(outstr,delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    outstr_s2s = io.StringIO()
    writer_s2s = csv.writer(outstr_s2s,delimiter=',',
                            quoting=csv.QUOTE_MINIMAL)

    for row in loginput:
        if linecount > 100000:
            break
        else:
            (fn,s2s,l) = toSOTAFLE(row)
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

    return(files)

def toWWFF_FLE(h):
    date = '{year:02}{month:02}{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])
    
    date2 = '{year:02}-{month:02}-{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year'])
    
    wwffref = h['mywwff']

    l = [
        adif('WWFFActivator',h['mycall']),
        adif('callsign',h['callsign']),
        adif('date',date),
        adif('time',
             '{hour:02}{minute:02}'.format(
                 hour=h['hour'], minute=h['min'])),
        adif('band-wlen',h['band']),
        adif('mode',h['mode']),
        adif('rst_sent',h['rst_sent']),
        adif('rst_rcvd',h['rst_rcvd']),
        adif('mysig','WWFF'),
        adif('mysiginfo',wwffref)
        ]
    
    if h['hiswwff'] != '':
        l+= [adif('sig','WWFF'),adif('siginfo',h['hiswwff'])]

    l+= [adif('WWFFOperator',h['operator']),'<EOR>']
    
    return (date2,wwffref,l)

def sendWWFF_FLE(files, loginput, callsign):
    outstr = io.StringIO()
    linecount = 0
    writer = csv.writer(outstr, delimiter=' ',
                        quoting=csv.QUOTE_MINIMAL)
    for row in loginput:
        if linecount > 100000:
            break
        else:
            (date,ref,l) = toWWFF_FLE(row)
            if linecount == 0:
                fname = callsign.replace('/','-') + '@' + ref + ' '+ date +'.adi'
                outstr.write('ADIF Export from FLEO by JL1NIE\n')
                outstr.write(adif('programid','FLEO')+'\n')
                outstr.write(adif('adifver','3.0.6')+'\n')
                outstr.write('<EOH>\n')
            writer.writerow(l)
            linecount += 1
    files.update({fname : outstr.getvalue()})

    return files

def toHamlog_FLE(h,rmksfl,env):
    date = '{year:02}/{month:02}/{day:02}'.format(
        day=h['day'], month=h['month'], year=h['year']%100)
    f = re.sub(r'[MHz|KHz|GHz]','',band_to_freq(h['band']))

    hisref = h['hissota']

    if h['hiswwff'] != '':
        hisref = hisref + "," + h['hiswwff']

    if rmksfl == 'hisref' :
        rmks1 = hisref
        rmks2 = env['qslmsg']
    else:
        rmks2 = hisref
        rmks1 = env['qslmsg']
        
    l = [
        h['callsign'],
        date,
        '{hour:02}:{minute:02}U'.format(hour=h['hour'], minute=h['min']),
        h['rst_sent'],
        h['rst_rcvd'],
        f,
        h['mode'],
        '',
        '',
        '',
        '',
        '',
        rmks1,
        rmks2,
        '0'
        ]
    
    return (l)

def sendHamlog_FLE(loginput, rmksfl, env):
    raw = io.BytesIO()
    outstr =io.TextIOWrapper(io.BufferedWriter(raw),
                             encoding='cp932',errors="backslashreplace")
    linecount = 0
    writer = csv.writer(outstr, delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    for row in loginput:
        if linecount > 100000:
            break
        else:
            l = toHamlog_FLE(row, rmksfl, env)
            writer.writerow(l)
            linecount += 1

    outstr.flush()
    return (raw.getvalue())

def toAirHamFLE(lcount, h, env):
    if lcount == 0:
        l= ["id","callsign","portable","qso_at","sent_rst",
            "received_rst","sent_qth","received_qth",
            "received_qra","frequency","mode","card",
            "remarks"]
        return l

    tstr ="{year:04}/{month:02}/{day:02} {hour:02}:{min:02} +0000".format(year=h['year'],month=h['month'],day=h['day'],hour=h['hour'],min=h['min'])
    atime = datetime.datetime.strptime(tstr,'%Y/%m/%d %H:%M %z')
    utime = atime.astimezone(datetime.timezone(datetime.timedelta(hours=0)))
    isotime = atime.isoformat()
    
    (operator, portable) = splitCallsign(h['callsign'])
    
    freq = band_to_freq(h['band'])
    freq_dec = re.sub(r'[MHz|KHz|GHz]','',freq)
    mode = mode_to_airhammode(h['mode'], freq_dec)

    hisref = []
    if h['hissota'] != '':
        hisref.append(h['hissota'])
        
    if h['hiswwff'] != '':
        hisref.append(h['hiswwff'])
                                         
    l = ["",
         operator,
         portable,
         isotime,
         h['rst_sent'],
         h['rst_rcvd'],
         env['qslmsg'],
         ",".join(hisref),
         "",
         freq,
         mode,
         "",
         ""
        ]
    return l

def sendAirHam_FLE(loginput, env):
    raw = io.BytesIO()
    outstr =io.TextIOWrapper(io.BufferedWriter(raw),
                             encoding='utf-8',errors="backslashreplace")
    linecount = 0
    writer = csv.writer(outstr, delimiter=',',
                        quoting=csv.QUOTE_MINIMAL)
    for row in loginput:
        if linecount > 100000:
            break
        else:
            if linecount == 0:
                writer.writerow(toAirHamFLE(linecount, row, env))
                linecount += 1
            writer.writerow(toAirHamFLE(linecount, row, env))
            linecount += 1

    outstr.flush()
    return (raw.getvalue())

def do_command(command, arg):
    res = {'status': "None" }
    if command == "interp":
        res = compileFLE(arg, False)
    print("Content-Type:application/json\n\n")
    print(json.dumps(res))
        
def main():
#    cgitb.enable(display=1, logdir='/tmp')

    form = cgi.FieldStorage()

    command = form.getvalue('command',None)
    arg = form.getvalue('arg',json.dumps("None"))
    text = form.getvalue('edittext',None)

    if command:
        if len(arg) < 131072:
            do_command(command,arg)
        else:
            print("Content-Type:application/json\n\n")
            print("<h4>Interal Error: Too many lines.</h4>\n\n")
    elif text:
        compileFLE(text, True)
    else:
        print("Content-Type:application/json\n\n")
        
if __name__ == '__main__':
    if not debug:
        main()
    else:
        f = open ("sample.fle","r")
        print(compileFLE(f.read(),False))
