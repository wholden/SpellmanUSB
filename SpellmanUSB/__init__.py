import hid
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)

hidhandle = None

setpointdict = {'kV Setpoint':{'setcmd':10,'getcmd':14,'scalefactor':50},
                        'mA Output Setpoint':{'setcmd':11,'getcmd':15,'scalefactor':2},
                        'Filament Preheat':{'setcmd':12,'getcmd':16,'scalefactor':10},
                        'Filament Limit':{'setcmd':13,'getcmd':17,'scalefactor':10}}
statusdict =  {'arg1':{'name':'hv',1:'HV on',0:'HV off'},
                    'arg2':{'name':'interlock',1:'Interlock Open',0:'Interlock Closed'},
                    'arg3':{'name':'fault',1:'Fault Condition',0:'No Fault'}}
monitordict = {'arg1':{'name':'Control Board Temperature(C)','scalefactor':300},
                    'arg2':{'name':'Low Voltage Supply Monitor (V)','scalefactor':42.9},
                    'arg3':{'name':'kV Feedback','scalefactor':50},
                    'arg4':{'name':'mA Feedback','scalefactor':2.4},
                    'arg5':{'name':'Filament Current(A)','scalefactor':3.6},
                    'arg6':{'name':'Filament Voltage(V)','scalefactor':5.5},
                    'arg7':{'name':'High Voltage Bd Temperature(C)','scalefactor':300}}

def initialize():
    global hidhandle
    hidhandle = hid.device()
    hidhandle.open(0x1200,0x001)
    hidhandle.set_nonblocking(1)
    
def calc_checksum(bytestr):
    strsum = np.sum([c for c in bytestr])
    chksum = ((((1<<32)+(~strsum+1)) & 255) & 127) | 64
    return chr(chksum).encode('ascii')

def make_cmdstr(cmd,arg=None):
    if arg is None:
        cmdstr = str(cmd)+','
    else:
        cmdstr = str(cmd)+','+str(arg)+','
    cmdstr = cmdstr.encode()
    chksum = calc_checksum(cmdstr)
    msgstr = b'\x02'+cmdstr+chksum+b'\x03'
    return [i for i in msgstr]

def parse_output(outbytelist):
    try:
        crop = outbytelist[1:outbytelist.index(3)]
    except ValueError:
        logger.Warning('Read error. Could not parse Spellman output string.')
        return 'readerr'
    outstr = ''.join([chr(c) for c in crop])
    assert calc_checksum(outstr[:-1].encode()) == outstr[-1].encode(), "Checksum error for USB-Spellman communication."
    responselist = outstr.split(',')
    responselist = responselist[1:-1]#remove chksum and cmd in response
    responsedict={}
    for i, v in enumerate(responselist):
        k='arg%d'%(i+1)
        try:
            responsedict[k]=int(v)
        except:
            responsedict[k]=v
    return responsedict

def sendrecv(cmd,arg=None):
    hidhandle.send_feature_report(make_cmdstr(cmd,arg))
    return parse_output(hidhandle.read(53,100))  

def monitor_readbacks():
    response = sendrecv(20)
    readbacks = {}
    for k, v in response.items():
        val = adc_scale(k,v)
        readbacks[monitordict[k]['name']]=val
    return readbacks
        
def adc_scale(key,val):
    return val*monitordict[key]['scalefactor']/4095

def dac_scale(key,val):
    return int(val*4095/setpointdict[key]['scalefactor'])

def dac_readback(key,val):
    return val/4095*setpointdict[key]['scalefactor']   

def check_setpoints():
    response = {}
    for k, v in setpointdict.items():
        response[k]=sendrecv(v['getcmd'])
    setpoints = {}
    for k, v in response.items():
        setpoints[k]=dac_readback(k,v['arg1'])
    return setpoints

def change_setpoint(key,val):
    dacvalue = dac_scale(key,val)
    response = sendrecv(setpointdict[key]['setcmd'],arg=dacvalue)
    if response['arg1'] == '$':
        print(key+' changed to: '+str(val))
    else:
        print('Error, setpoint not changed.')
    return response

def engage_high_voltage():
    response = sendrecv(99,arg=1)
    if response['arg1'] == '$':
        print('High voltage ON.')
    elif response['arg1'] == '1':
        print('Programming error, high voltage NOT engaged.')
    elif response['arg1'] == '0':
        print('Interlock is open, high voltage disabled.')
    return response['arg1']

def disengage_high_voltage():
    response = sendrecv(99,arg=0)
    if response['arg1'] == '$':
        print('High voltage OFF.')
    elif response['arg1'] == '1':
        print('Programming error, high voltage NOT engaged.')
    elif response['arg1'] == '0':
        print('Interlock is open, high voltage disabled.')
    return response['arg1']

def reset_faults():
    response = sendrecv(52)
    return response['arg1']

def request_status():
    response = sendrecv(22)
    status={}
    for k, v in response.items():
        status[statusdict[k]['name']]=v
        print(statusdict[k][v])
    return status

def close_usb_connection():
    hidhandle.close()

def clear_setpoints():
    change_setpoint('Filament Limit',0)
    change_setpoint('Filament Preheat',0)
    change_setpoint('kV Setpoint',0)
    change_setpoint('mA Output Setpoint',0)

