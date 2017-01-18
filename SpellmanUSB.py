import hid
import time
import numpy as np

class Spellman():
    
    def __init__(self):
        self.h = hid.device()
        self.h.open(0x1200,0x001)
        self.h.set_nonblocking(1)
        self.adcscaledict = dict([('kV Feedback',50),
                                ('kV Feedback 2',55),
                                ('mA Feedback',2.4),
                                ('Filament Current(A)', 3.6),
                                ('Filament Voltage(V)',5.5),
                                ('Control Board Temperature(C)',300),
                                ('High Voltage Bd Temperature(C)',300),
                                ('Low Voltage Supply Monitor (V)',42.9)])
        self.dacscaledict=dict([('kV Setpoint',50),
                              ('mA Output Setpoint',2),
                              ('Filament Preheat',10),
                              ('Filament Limit',10)])
        self.cmddict=dict([(14,'Request kV Setpoint'),
                           (15,'Request mA Output Setpoint'),
                           (16,'Request Filament Preheat'),
                           (17,'Request Filament Limit')])
        
    def calc_checksum(self,bytestr):
        strsum = np.sum([c for c in bytestr])
        chksum = ((((1<<32)+(~strsum+1)) & 255) & 127) | 64
        return chr(chksum).encode('ascii')
    
    def make_cmdstr(self,cmd,arg=None):
        if not arg:
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
        responsedict = dict(cmd=int(responselist.pop(0)),chksum=responselist.pop())
        for i, v in enumerate(responselist):
            k='arg%d'%(i+1)
            responsedict[k]=int(v)
        return responsedict
    
    def monitor(self):
        self.h.send_feature_report(self.make_cmdstr(20))
        output = self.h.get_feature_report(1,27)
        responsedict = self.parse_output(output)
        msgdict = dict(arg1 = 'Control Board Temperature(C)',
                   arg2 = 'Low Voltage Supply Monitor (V)',
                   arg3 = 'kV Feedback',
                   arg4 = 'mA Feedback',
                   arg5 = 'Filament Current(A)',
                   arg6 = 'Filament Voltage(V)',
                   arg7 = 'High Voltage Bd Temperature(C)')
        for k,v in msgdict.items():
            print(msgdict[k]+'\t'+str(self.adc_scale(responsedict[k],v)))
            
    def adc_scale(self,val,key):
        return val*self.adcscaledict[key]/4095
    
    def dac_scale(self,val,key):
        return int(val*4095/self.dacscaledict[key])
    
    def sendrecv(self,cmd,arg=None):
        self.h.send_feature_report(self.make_cmdstr(cmd,arg))
        return self.parse_output(self.h.read(53,100))     
    
    def request_setpoints(self):
        response = [self.sendrecv(i) for i in (14,15,16,17)]
        for r in response:
            print(self.cmddict[r['cmd']]+': '+str(self.dac_scale(r['arg1'],self.cmddict[r['cmd']][8:])))
        return response
    
    def change_setpoint(self,name,value):
        dacvalue = self.dac_scale(value,name)
        response = self.sendrecv(13,arg=dacvalue)
        return response
