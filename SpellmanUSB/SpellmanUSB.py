import hid
import time
import numpy as np

class SpellmanClass():
    
    def __init__(self):
        self.h = hid.device()
        self.h.open(0x1200,0x001)
        self.h.set_nonblocking(1)
        self.setpointdict = {'kV Setpoint':{'setcmd':10,'getcmd':14,'scalefactor':50},
                                'mA Output Setpoint':{'setcmd':11,'getcmd':15,'scalefactor':2},
                                'Filament Preheat':{'setcmd':12,'getcmd':16,'scalefactor':10},
                                'Filament Limit':{'setcmd':13,'getcmd':17,'scalefactor':10}}
        self.statusdict =  {'arg1':{1:'HV on',0:'HV off'},
                            'arg2':{1:'Interlock Open',0:'Interlock Closed'},
                            'arg3':{1:'Fault Condition',0:'No Fault'}}
        self.monitordict = {'arg1':{'name':'Control Board Temperature(C)','scalefactor':300},
                            'arg2':{'name':'Low Voltage Supply Monitor (V)','scalefactor':42.9},
                            'arg3':{'name':'kV Feedback','scalefactor':50},
                            'arg4':{'name':'mA Feedback','scalefactor':2.4},
                            'arg5':{'name':'Filament Current(A)','scalefactor':3.6},
                            'arg6':{'name':'Filament Voltage(V)','scalefactor':5.5},
                            'arg7':{'name':'High Voltage Bd Temperature(C)','scalefactor':300}}
        
    def calc_checksum(self,bytestr):
        strsum = np.sum([c for c in bytestr])
        chksum = ((((1<<32)+(~strsum+1)) & 255) & 127) | 64
        return chr(chksum).encode('ascii')
    
    def make_cmdstr(self,cmd,arg=None):
        if arg is None:
            cmdstr = str(cmd)+','
        else:
            cmdstr = str(cmd)+','+str(arg)+','
        cmdstr = cmdstr.encode()
        chksum = self.calc_checksum(cmdstr)
        msgstr = b'\x02'+cmdstr+chksum+b'\x03'
        return [i for i in msgstr]
    
    def parse_output(self,outbytelist):
        crop = outbytelist[1:outbytelist.index(3)]
        outstr = ''.join([chr(c) for c in crop])
        assert self.calc_checksum(outstr[:-1].encode()) == outstr[-1].encode(), "Checksum error for USB-Spellman communication."
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

    def sendrecv(self,cmd,arg=None):
        self.h.send_feature_report(self.make_cmdstr(cmd,arg))
        return self.parse_output(self.h.read(53,100))  
    
    def monitor_readbacks(self):

        response = self.sendrecv(20)
        for k, v in response.items():
            val = self.adc_scale(k,v)
            print(self.monitordict[k]['name']+': '+str(val))
            
    def adc_scale(self,key,val):
        return val*self.monitordict[key]['scalefactor']/4095
    
    def dac_scale(self,key,val):
        return int(val*4095/self.setpointdict[key]['scalefactor'])

    def dac_readback(self,key,val):
        return val/4095*self.setpointdict[key]['scalefactor']   
    
    def check_setpoints(self):
        response = {}
        for k, v in self.setpointdict.items():
            response[k]=self.sendrecv(v['getcmd'])
        for k, v in response.items():
            print('Current '+k+': '+str(self.dac_readback(k,v['arg1'])))
        return response
    
    def change_setpoint(self,key,val):
        # Still a work in progress here
        dacvalue = self.dac_scale(key,val)
        response = self.sendrecv(self.setpointdict[key]['setcmd'],arg=dacvalue)
        if response['arg1'] == '$':
            print(key+' changed to: '+str(val))
        else:
            print('Error, setpoint not changed.')
        return response

    def engage_high_voltage(self):
        response = self.sendrecv(99,arg=1)
        if response['arg1'] == '$':
            print('High voltage ON.')
        elif response['arg1'] == '1':
            print('Programming error, high voltage NOT engaged.')
        elif response['arg1'] == '0':
            print('Interlock is open, high voltage disabled.')
        return response['arg1']

    def disengage_high_voltage(self):
        response = self.sendrecv(99,arg=0)
        if response['arg1'] == '$':
            print('High voltage OFF.')
        elif response['arg1'] == '1':
            print('Programming error, high voltage NOT engaged.')
        elif response['arg1'] == '0':
            print('Interlock is open, high voltage disabled.')
        return response['arg1']

    def reset_faults(self):
        response = self.sendrecv(52)
        return response['arg1']

    def request_status(self):
        response = self.sendrecv(22)
        for k, v in response.items():
            print(self.statusdict[k][v])
    
    def close_usb_connection(self):
        self.h.close()

    def clear_setpoints(self):
        self.change_setpoint('Filament Limit',0)
        self.change_setpoint('Filament Preheat',0)
        self.change_setpoint('kV Setpoint',0)
        self.change_setpoint('mA Output Setpoint',0)

    def initialize_setpoints(self):
        self.change_setpoint('Filament Limit',3.1)
        self.change_setpoint('Filament Preheat',1.5)
        self.change_setpoint('kV Setpoint',25)
        self.change_setpoint('mA Output Setpoint',1)

spellman = SpellmanClass()