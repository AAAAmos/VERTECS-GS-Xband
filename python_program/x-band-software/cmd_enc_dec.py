import sys

#file_name = 'F20540802065959.bin'
#id_start = 16000
#id_end = 19000
#name = 'IM' #'HK'/'IMG'


#######################################################################
def make_command(file_name,name,id_start,id_end):
    #F20YYMMDDhhmmss
    YY = int(file_name[3:5] )
    MM = int(file_name[5:7] )
    DD = int(file_name[7:9] )
    hh = int(file_name[9:11] )
    mm = int(file_name[11:13])
    ss = int(file_name[13:15])
    out_date = YY.to_bytes(1,'big')+MM.to_bytes(1,'big')\
        +DD.to_bytes(1,'big')+(ss+60*(mm+60*hh)).to_bytes(3,'big')

    if name == 'HK':
        label=0
        out_name = label.to_bytes(1,'big')
        out_ids = id_start.to_bytes(2,'big') + id_end.to_bytes(2,'big')
    elif name == 'IM':
        label=1
        out_name = label.to_bytes(1,'big')
        out_ids = id_start.to_bytes(2,'big') + id_end.to_bytes(2,'big')
    elif name == 'OK':
        label=2
        out_name = label.to_bytes(1,'big')
        id_temp = 0
        out_ids = id_temp.to_bytes(2,'big') + id_temp.to_bytes(2,'big')
    elif name == 'Error':
        label=3
        out_name = label.to_bytes(1,'big')
        id_temp = 65535
        out_ids = id_temp.to_bytes(2,'big') + id_temp.to_bytes(2,'big')
    else:
        print('ERROR: unknown label')
        print(name)
        sys.exit(2)
        
    return out_date + out_name + out_ids

######################################################################
def decode_command(com):
    #F20YYMMDDhhmmss
    YY = str(com[0]).zfill(2)
    MM = str(com[1]).zfill(2)
    DD = str(com[2]).zfill(2)
    t = int.from_bytes(com[3:6],'big')
    ss = t%60
    mm = int((t-ss)/60)%60
    hh = int((t-ss-60*mm)/3600)

    file_name = 'F20'+\
        YY + MM + DD + \
        str(hh).zfill(2) + str(mm).zfill(2) + str(ss).zfill(2) +\
            '.dat'
    
    if com[6] == 0:
        label = 'HK'
    elif com[6] == 1:
        label = 'IMG'
    else:
        label = 'UNKNOWN'

    id_start=int.from_bytes(com[7:9],'big')
    id_end=int.from_bytes(com[9:11],'big')

    return [file_name,label,id_start,id_end]
