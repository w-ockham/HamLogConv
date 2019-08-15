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
        myqth = options['Summit']
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
    
def toSOTA(lcount, row, options):
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
        options['Activator'],
        options['Summit'],
        '{day:02}/{month:02}/{year:02}'.format(day=h['day'], month=h['month'], year=h['year']),
        '{hour:02}:{minute:02}'.format(hour=h['hour'], minute=h['minute']),
        h['band'],
        h['mode'],
        h['callsign'],
        hisqth,
        comment
    ]
    print(",".join(l))
    
def toADIF(lcount, row, options):
    if lcount == 0:
        return None
    
    h = decodeHamlog(row)
    return row
    
def main():
    cgitb.enable()
    response =u"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
<title> File conversion tool for AirHamLog beta.</title>
    </head>

    <body>
    <div class="header clearfix">
    <h6 class="text-muted"> File Conversion Tool for AirHamLog beta.</h6>
    </div>
    <form method="post" enctype="multipart/form-data" action='conversion.py' style="padding:10px">
    <div class="form-row">
     <div class="form-group col-sm-6">
       <label for="inftype">アップロードするファイルの形式</label>
       <select id="inftype" name="inftype" class="form-control">
         <option> HamLog CSV </option>
       </select>
     </div>
     <div class="form-group col-sm-6">
       <label for="outftype">変換後のファイルの形式</label>
       <select id="outftype" name="outftype" class="form-control">
         <option>AirHamLog CSV</option>
         <option>SOTA CSV</option>
         <option>ADIF</option>
       </select>
     </div>
    </div>
    <div class="form-row">
    <div class="form-group col-sm-6">
    <div class="form-check">
      <input class="form-check-input" type="radio" name="QTH" id="QTHNone" value="none" checked>
      <label class="form-check-label" for="QTHNone">
      指定しない
      </label>
    </div>
    <div class="form-check">
      <input class="form-check-input" type="radio" name="QTH" id="QTH1" value="rmks1">
      <label class="form-check-label" for="QTH1">
      Remarks1を送信QTHにする
      </label>
    </div>
    <div class="form-check">
      <input class="form-check-input" type="radio" name="QTH" id="QTH2" value="rmks2">
      <label class="form-check-label" for="QTH2">
      Remarks2を送信QTHにする
      </label>
    </div>
    <div class="form-check">
      <input class="form-check-input" type="radio" name="QTH" id="QTH3" value="user_defined">
      <label class="form-check-label" for="QTH2">
      移動運用先を送信QTHにする
      </label>
    </div>
    </div>

    <div class ="form-group col-sm-6">
    <label for="your_call">移動運用時のコールサイン</label>
    <input type="text" id="your_call" name="your_call" class="form-control" placeholder="コールサイン">
    <label for="summit">移動運用先(JCC/JCG/SOTA山岳ID/JAFFリファレンスなど)</label>
    <input type="text" id="summit" name="summit" class="form-control" placeholder="SOTA Summit or JAFF References (e.g. JA/NN-031 JAFF-0056)">
    </div>
    </div>

    <div class="form-group">
    <div class="custom-file">
    <input type="file" class="custom-file-input" id="filename" name="filename" required>
    <label class="custom-file-label" for="filename">ファイルを選択</label>
    <div class="invalid-feedback">ファイルを指定してください</div>
    </div>
    </div>

    <div class="form-group">
    <button type="submit" class="btn btn-primary">アップロード</button>
    </div>
    </form>
    <!-- Option Javascript -->
    <script src="https://code.jquery.com/jquery-3.4.0.min.js" integrity="sha256-BJeo0qm959uMBGb65z40ejJYGSgR7REI4+CW1fNKwOg=" crossorigin="anonymous"> </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    
    <script>
    $('.custom-file-input').on('change',function(){
    $(this).next('.custom-file-label').html($(this)[0].files[0].name);
    })
    </script>
    </body>
    </html>
    """

    form = cgi.FieldStorage()
    inftype = form.getvalue('inftype',None)
    outftype = form.getvalue('outftype',None)

    options = {
        'QTH': form.getvalue('QTH',None),
        'Activator': form.getvalue('your_call',None),
        'Summit': form.getvalue('summit',None)
    }
    
    if "filename" not in form:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        print('Content-type: text/html; charset=UTF-8\n')
        print(response)
    else:
        fileitem = form['filename']
        now  = datetime.datetime.now()
        fname = now.strftime("%Y-%m-%d-%H-%M")

        if "HamLog" in inftype:
            incharset = 'cp932'
        else:
            incharset = 'utf-8'
            
        if "AirHamLog" in outftype:
            outcharset = "utf-8"
            fname = "airhamlog-" + fname + ".csv"
            convfunc = toAirHam
        elif "SOTA" in outftype:
            outcharset = "utf-8"
            fname = "sota-" + fname + ".csv"
            convfunc = toSOTA
        else:
            outcharset = "utf-8"
            fname = "adif-" + fname + ".csv"
            convfunc = toADIF

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
                            header = convfunc(linecount, row, options)
                            if header:
                                writer.writerow(header)
                                linecount += 1
                        writer.writerow(convfunc(linecount, row, options))
                        linecount += 1

        else:
            print('Content-type: text/html; charset=utf-8\n')
            print('<h1> File not found:%s' % fileitem)
            
if __name__ == '__main__':
    main()

