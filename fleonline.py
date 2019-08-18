#!/usr/bin/env python3
# coding: utf-8
import cgi
import cgitb
import datetime
import io
import json
import re
import sys
from convutil import (
    writeZIP,
    freq_to_band,
    band_to_freq
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
    'date':1
}

def keyword(key):
    try:
        arg = keyword_table[key.lower()]
    except Exception as e:
        return None
    return((key.lower(),arg))

mode_table = {
    'cw':0,
    'ssb':0,
    'fm':0,
}

def modes(key):
    try:
        arg = mode_table[key.lower()]
    except Exception as e:
        return None
    return(key.upper())
    
def tokenizer(line):
    res = []
    words = line.split()
    for word in words:
        w = word.upper()
        if w[0] == '#':
            break
        m = re.match('(\d+)-(\d+)-(\d+)',w)
        if m:
            res.append(('date',(m.group(1),m.group(2),m.group(3)),w))
            continue
        m = re.match('(\d+)-(\d+)',w)
        if m:
            res.append(('date2',(m.group(1),m.group(2)),w))
            continue
        m = re.match('(\d+)/(\d+)/(\d+)',w)
        if m:
            res.append(('date',(m.group(1),m.group(2),m.group(3)),w))
            continue
        m = re.match('(\d+)/(\d+)',w)
        if m:
            res.append(('date2',(m.group(1),m.group(2)),w))
            continue
        m = re.match('\d+\.\d+',w)
        if m:
            res.append(('freq',freq_to_band(w),w))
            continue
        m = re.match('-\d+',w)
        if m:
            res.append(('snr',w,w))
            continue
        bd = band_to_freq(w)
        if bd:
            res.append(('band',bd,word))
            continue
        m = re.match('\d+',w)
        if m:
            res.append(('dec',len(w),w))
            continue
        m = re.match('\w+FF-\d+',w)
        if m:
            res.append(('wwffref',w,word))
            continue
        m = re.match('\w+/\w+-\d+',w)
        if m:
            res.append(('sotaref',w,word))
            continue
        kw = keyword(w)
        if kw:
            res.append(('kw',kw,word))
            continue
        md = modes(w)
        if md:
            res.append(('md',md,word))
            continue
        res.append(('id',w.upper(),word))
    return(res)

def compileFLE(text):
    res = []
    (NORM,FREQ,RSTS,RSTR)=(1,2,3,4)
    env = {
        'mycall':'JL1NIE',
        'operator':'JL1NIE',
        'qslmsg':'',
        'mywwff':'',
        'mysota':'',
        'nickname':'',
        'current_year':2000,
        'current_month':1,
        'current_day':1,
        'current_hour':0,
        'current_min':0,
        'current_mode':'cw',
        'current_band':'20m',
        'current_freq':'14.062',
        'current_call':'',
        'current_his_wwff':'',
        'current_his_sota':'',
        'current_r_s':5,
        'current_s_s':9,
        'current_t_s':9,
        'current_r_r':5,
        'current_s_r':9,
        'current_t_r':9,
        'errorno':[]
    }
    
    lines = text.splitlines()
    lc = 1
    qsoc = 0
    sotafl = False
    wwfffl = False
    for l in lines:
        env['current_r_s']=5
        env['current_s_s']=9
        env['current_t_s']=9
        env['current_r_r']=5
        env['current_s_r']=9
        env['current_t_r']=9
        env['cuurent_call']=''
        env['current_his_wwff']=''
        env['current_his_sota']=''
        tl = tokenizer(l)
        pos = 0
        if not tl:
            continue
        (t,p1,p2) = tl[pos]
        if t == 'kw':
            (key, l) = p1
            if key == 'mycall':
                (id, call, w) = tl[pos+1]
                if id =='id':
                    env['mycall'] = call
                else:
                    errno.append(lc,pos+1,w)
                lc += 1
                continue
            if key == 'operator':
                (id, op, w) = tl[pos+1]
                if id =='id':
                    env['operator'] = op
                else:
                    errno.append(lc,pos+1,w)
                lc += 1
                continue
            if key == 'mywwff':
                (id, ref, w) = tl[pos+1]
                if id =='wwffref':
                    env['mywwff'] = ref
                    wwfffl = True
                else:
                    env['errno'].append(lc,pos+1,w)
                lc += 1
                continue
            if key == 'mysota':
                (id, ref, w) = tl[pos+1]
                if id =='sotaref':
                    env['mysota'] = ref
                    sotafl = True
                else:
                    env['errno'].append(lc,pos+1,w)
                lc += 1
                continue
            if key == 'nickname':
                (_, _, w) = tl[pos+1]
                env['nickname'] = w
                lc += 1
                continue
            if key == 'qslmsg':
                msg = ""
                for i in range(len(tl)-1):
                    (_ , _, w) = tl[i+1]
                    msg = msg + " " + w
                env['qslmsg'] = msg
                lc += 1
                continue
            if key == 'date':
                (d, dp, w) = tl[pos+1]
                if d =='date':
                    (y,m,d) = dp
                    env['current_year'] = int(y)
                    env['current_month'] = int(m)
                    env['current_day'] = int(d)
                elif d =='date2':
                    (m,d) = dp
                    env['current_month'] = int(m)
                    env['current_day'] = int(d)
                else:
                    env['errno'].append((lc,pos+1,w))
                lc += 1
                continue
        else:
            length = len(tl)
            state = NORM

            while pos < length:
                (t,p1,p2) = tl[pos]
                if state == NORM:
                    if t == 'md':
                        env['current_mode'] = p1
                        state = NORM
                        pos += 1
                        continue
                    if t == 'band':
                        env['current_band'] =p2
                        state = FREQ
                        pos += 1
                        continue
                    if t == 'dec':
                        if p1 == 1:
                            env['current_min'] = int(env['current_min']//10)*10 + int(p2)
                        elif p1 ==2:
                            env['current_min'] = int(p2) % 60
                        elif p1 == 3:
                            h = int(p2) // 100
                            m = int(p2) % 60
                            env['current_hour'] = int(env['current_hour']//10)*10 + h
                            env['current_min'] = m
                        elif p1 == 4:
                            h = int(p2) // 100
                            m = int(p2) %100 % 60
                            env['current_hour'] = h
                            env['current_min'] = m
                        else:
                            env['errno'].append((lc,pos,p2))
                        pos+=1
                        state = NORM
                        continue
                    if t == 'wwffref':
                        env['current_his_wwff'] = p1
                        pos+=1
                        state = NORM
                        continue
                    if t == 'sotaref':
                        env['current_his_sota'] = p1
                        pos+=1
                        state = NORM
                        continue
                    if t == 'id':
                        env['current_call'] = p1
                        pos+=1
                        qsoc+=1
                        state = RSTS
                        continue
                    else:
                        pos+=1
                        state = NORM
                elif state == FREQ:
                    if t == 'freq':
                        env['current_freq'] = p2
                        pos+=1
                        state = NORM
                        continue
                    else:
                        state = NORM
                        continue
                elif state == RSTS:
                    if t == 'dec':
                        if p1 == 1:
                            env['current_s_s'] = int(p2)
                            pos += 1
                            state = RSTR
                            continue
                        elif p1 == 2:
                            env['current_r_s'] = int(p2)//10
                            env['current_s_s'] = int(p2)%10
                            pos += 1
                            state = RSTR
                            continue
                        elif p1 == 3:
                            env['current_r_s'] = int(p2)//100
                            env['current_s_s'] = (int(p2)%100)//10
                            env['current_t_s'] = int(p2)%10
                            pos += 1
                            state = RSTR
                            continue
                    else:
                        state = NORM
                        continue
                elif state == RSTR:
                    if t == 'dec':
                        if p1 == 1:
                            env['current_s_r'] = int(p2)
                            pos += 1
                            state = NORM
                            continue
                        elif p1 == 2:
                            env['current_r_r'] = int(p2)//10
                            env['current_s_r'] = int(p2)%10
                            pos += 1
                            state = NORM
                            continue
                        elif p1 == 3:
                            env['current_r_r'] = int(p2)//100
                            env['current_s_r'] = (int(p2)%100)//10
                            env['current_t_r'] = int(p2)%10
                            pos += 1
                            state = NORM
                            continue
                    else:
                        state = NORM
                        continue
            lc+=1
        if env['current_call'] != '':
            mycall = env['mycall']
            call = env['current_call']
            date = '{y:02}-{m:02}-{d:02}'.format(y=env['current_year'],m=env['current_month'],d=env['current_day'])
            time = '{h:02}:{m:02}'.format(h=env['current_hour'],m=env['current_min'])
            band = env['current_band']
            mode = env['current_mode']
            rsts = str(env['current_r_s']*100+env['current_s_s']*10+env['current_t_s'])
            rstr = str(env['current_r_r']*100+env['current_s_r']*10+env['current_t_r'])
            mysota = env['mysota']
            hissota = env['current_his_sota']
            mywwff = env['mywwff']
            hiswwff = env['current_his_wwff']
            operator = env['operator']
            qso = [ qsoc, mycall, date, time, call, band, mode, rsts, rstr, mysota, hissota,mywwff, hiswwff ,operator]
            res.append(qso)
            
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

    res = {'status': status,
           'logtype': logtype,
           'logtext': logtext
    }
    return (res)

def do_command(command, arg):
    res = {'status': "None" }
    if command == "interp":
        res = compileFLE(arg)
    print("Content-Type:application/json\n\n")
    print(json.dumps(res))
        
def generateLog(text):
    now  = datetime.datetime.now()
    fnamezip = "fle-" + now.strftime("%Y-%m-%d-%H-%M") +".zip"
    fnameorg = "flelog" + now.strftime("%Y-%m-%d-%H-%M") +".txt"
    fnamecsv = "sota-" + now.strftime("%Y-%m-%d-%H-%M") +".csv"
    
    res = compileFLE(text)
    loglist = res['logtext']
    
    files = {
        fnameorg:text,
        fnamecsv:"".join(loglist)
        }
    writeZIP(files,fnamezip)
        
def main():
#    cgitb.enable(display=1, logdir='/tmp')

    form = cgi.FieldStorage()

    command = form.getvalue('command',None)
    arg = form.getvalue('arg',json.dumps("None"))
    text = form.getvalue('edittext',None)

    if debug:
        command = "interp"
        arg = "Quick\n Brown\n Fox\n Jumps\n Over\n The\n Lazu\n Dog.\n"
        
    if command:
        do_command(command,arg)
    elif text:
        generateLog(text)
    else:
        print("Content-Type:application/json\n\n")
        
if __name__ == '__main__':
    main()
    #l ="mycall jl1nie/1\n operator jl1nie\n mywwff jaff-0202\n"+"mysota ja/kn-032\n nickname tom \n qslmsg Hello 123 Myname\ndate 2019-1-1\n date 11/2\n"+"2230 jl1nie\n 9 jj1swi 9\n 20 jp1qec 4 4\n"
    #r = compileFLE(l)
    #print(r)
  
