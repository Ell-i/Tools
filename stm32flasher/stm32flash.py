#! /usr/bin/env python

"""
Copyright (c) 2013, Antti Louko
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Antti Louko.
"""

import sys
import getopt
import os
import serial
import select
import time
import operator
import struct
import intelhex

def usage(utyp, *msg):
    sys.stderr.write('''Usage: %s [-hbrwAN] /dev/ttyUSB0
    -b rate       serial speed in bits/s
    -r filename   Read flash to ihex file
    -w filename   Write file to flash
    -A 0x........ Start address (for reading, write honours ihex file)
    -N npages     Number of KiBs to read
\n''' % os.path.split(sys.argv[0])[1])
    if msg:
        sys.stderr.write('Error: %s\n' % `msg`)
    sys.exit(1)

def i2nbytes(i,nbytes):
    return struct.pack('>Q',i)[-nbytes:]

def return_flush(ser,r=None):
    ser.flushInput()
    ser.flushOutput()
    ser.flush()
    time.sleep(0.1)
    return r

class STM32flash:
    def __init__(self):
        self.filename = None
        self.speed = 57600
        self.op = None
        self.addr = 0x08000000
        self.npages = 1

        return

    def read_n(self,ser,toread=1):
        "Read at most toread bytes from ser"
        nread = 0
        a = []
        while nread < toread:
            rin = [ser.fd]
            iwtd, owtd, ewtd = select.select(rin,[],[],2.0)
            nn = 0
            if ser.fd in iwtd:
                nn = nn+1
                n = min(toread-nread,ser.inWaiting())
                try:
                    d = ser.read(n)
                except OSError:
                    break
                if d:
                    a.append(d)
                    nread += len(d)
            if not nn:
                break
        return ''.join(a)

    ACK = '\x79'
    NACK = '\x1f'

    CMD_GET = 0x00
    CMD_GETVERSION = 0x01
    CMD_GETID = 0x02
    CMD_READMEM = 0x11
    CMD_GO = 0x21
    CMD_WRITEMEM = 0x31
    CMD_ERASE = 0x43
    CMD_EERASE = 0x44
    CMD_WRPROTECT = 0x63
    CMD_WRUNPROTECT = 0x73
    CMD_RDPROTECT = 0x82
    CMD_RDUNPROTECT = 0x92

    def cksum(self,data,xtra=0xff):
        "Xor checksum of string data and xtra argument"
        return xtra ^ reduce(operator.xor,[ord(i) for i in data])

    def sendcksum(self,ser,bytes,xtra=0xff,v=False):
        dsend = '%s%c' % (bytes,self.cksum(bytes,xtra))
        if v: self.ferr.write('sendcksum %s\n' % (repr(dsend),))
        ser.write(dsend)
        return

    def check_ack(self,ser,rr=[None]):
        ack = self.read_n(ser,1)
        if ack == self.NACK:
            r = 'NACK'
        elif ack != self.ACK:
            return_flush(ser)
            r = 'Not ACK'
        else:
            r = None
        if r:
            rr[0] = r
            return False
        else:
            return True

    def cmd_get(self,ser):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_GET))
        if not self.check_ack(ser,rr):
            return False,rr[0]

        nbytes = self.read_n(ser,1)
        nbytes = ord(nbytes)+1
        d = self.read_n(ser,nbytes)

        if not self.check_ack(ser,rr):
            return False,rr[0],d

        return True,d

    def cmd_get_version(self,ser):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_GETVERSION))
        if not self.check_ack(ser,rr):
            return False,rr[0]

        d = self.read_n(ser,3)

        if not self.check_ack(ser,rr):
            return False,rr[0],d

        return True,d

    def cmd_get_id(self,ser):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_GETID))
        if not self.check_ack(ser,rr):
            return False,rr[0]

        nbytes = self.read_n(ser,1)
        nbytes = ord(nbytes)+1
        d = self.read_n(ser,nbytes)

        if not self.check_ack(ser,rr):
            return False,rr[0],d

        return True,d

    def cmd_read_mem(self,ser,addr,dsize):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_READMEM))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        self.sendcksum(ser,i2nbytes(addr,4),0x00)
        if not self.check_ack(ser,rr):
            return False,rr[0],2

        self.sendcksum(ser,i2nbytes(dsize-1,1),0xff)
        if not self.check_ack(ser,rr):
            return False,rr[0],3

        d = self.read_n(ser,dsize)

        return True,d

    def cmd_go(self,ser,addr):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_GO))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        self.sendcksum(ser,i2nbytes(addr,4),0x00)

        if not self.check_ack(ser,rr):
            return False,rr[0],2

        if not self.check_ack(ser,rr):
            return False,rr[0],3

        return True,

    def cmd_write_mem(self,ser,addr,data):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_WRITEMEM))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        self.sendcksum(ser,i2nbytes(addr,4),0x00)
        if not self.check_ack(ser,rr):
            return False,rr[0],2

        data2 = chr(len(data)-1) + data
        self.sendcksum(ser,data2,0x00)
        if not self.check_ack(ser,rr):
            return False,rr[0],3

        return True,len(data)

    def cmd_erase(self,ser,pages):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_ERASE))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        if pages == 255:
            self.sendcksum(ser,chr(0xff))
            if not self.check_ack(ser,rr):
                return False,rr[0],2
            return True,
        else:
            pages = ''.join([chr(i) for i in pages])
            data2 = chr(len(pages)-1) + pages
            self.sendcksum(ser,data2)
            if not self.check_ack(ser,rr):
                return False,rr[0],3
            return True,

    def cmd_extended_erase(self,ser,pages):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_EERASE))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        if (type(pages) in (type(1),type(1l)) and
            pages >= 0xfff0 and pages <= 0xffff):
            data = struct.pack('>H',pages)
            self.sendcksum(ser,data,0x00)
            if not self.check_ack(ser,rr):
                return False,rr[0],3
            return True,
        else:
            pages = list(pages)
            pages.insert(0,len(pages)-1)
            data = [struct.pack('>H',i) for i in pages]
            data2 = ''.join(data)
            self.sendcksum(ser,data2,0x00)
            if not self.check_ack(ser,rr):
                return False,rr[0],3
            return True,

    def cmd_write_protect(self,ser,pages):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_WRPROTECT))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        pages = ''.join([chr(i) for i in pages])
        data2 = chr(len(pages)-1) + pages
        self.sendcksum(ser,data2)
        if not self.check_ack(ser,rr):
            return False,rr[0],3
        return True,

    def cmd_write_unprotect(self,ser):
        rr = [None]
        self.sendcksum(ser,chr(self.CMD_WRUNPROTECT))
        if not self.check_ack(ser,rr):
            return False,rr[0],1

        if not self.check_ack(ser,rr):
            return False,rr[0],3
        return True,


    def reset(self,ser,bootloader=1):
        if bootloader:
            ser.setBreak(1);
            time.sleep(0.2);
            ser.setRTS(1)
            ser.setDTR(1)
            time.sleep(0.05);
            ser.setBreak(0)
            time.sleep(0.05);
            ser.setRTS(0)
            time.sleep(0.05);
            ser.setDTR(0)
        else:
            ser.setRTS(0)
            ser.setDTR(0)
            ser.setBreak(0)
            ser.setRTS(1)
            time.sleep(0.05);
            ser.setRTS(0)
            time.sleep(0.05);
            ser.setBreak(1)
            time.sleep(0.2);
            ser.setBreak(0)

        ser.flushInput()


    def doit(self,args):
        fin = sys.stdin
        fout = sys.stdout
        self.fout = fout
        self.ferr = sys.stderr

        if not args:
            usage(1, )

        port = args.pop(0)

        ser = serial.Serial(port, self.speed, parity=serial.PARITY_EVEN)

        ser.close()
        ser.open()

        self.reset(ser,bootloader=1)

        ser.write('%c' % (0x7f,))

        d = self.read_n(ser,1)

        r = self.cmd_get(ser)
        cmds = ' '.join(['%02x' % (ord(c),) for c in r[1]])
        fout.write('Get: %s\n' % (cmds,))

        r = self.cmd_get_version(ser)
        fout.write('Get version: %s\n' % (r,))

        r = self.cmd_get_id(ser)
        fout.write('Get id: %s\n' % (r,))

        a0 = self.addr
        a1 = a0 + self.npages*1024

        if self.op == 'r':
            ff = file(self.filename,'wb')
            i1 = intelhex.IntelHex()
            for a in xrange(a0,a1,256):
                r = self.cmd_read_mem(ser,a,256)
                if r[0]:
                    d = r[1]
                else:
                    d = ''
                    fout.write('Read mem: %s\n' % (r,))
                fout.write('Read mem: %08x  %3d\n' % (a,len(d)))
                i1[a:a+len(d)] = [ord(c) for c in d]
            i1.tofile(ff,'hex')
            ff.close()

        elif self.op == 'w':
            ff = file(self.filename,'rb')

            i1 = intelhex.IntelHex()
            i1.loadfile(ff,'hex')

            i2 = intelhex.IntelHex(i1)

            r = self.cmd_extended_erase(ser,0xffff)
            if not r[0]:
                fout.write('Erase failed %s\n' % (r[1:],))
                return 1

            while i2.minaddr() < i2.maxaddr():
                a1 = i2.minaddr()
                a2 = a1+0x100
                flashdata = i2[a1:a2].tobinstr()
                del i2[a1:a2]
                fout.write('%08x %4d %s\n' % (a1,len(flashdata),flashdata.encode('hex')[:32]))
                r = self.cmd_write_mem(ser,a1,flashdata)
                if not r[0]:
                    fout.write('Write failed %s\n' % (r[1:],))
                    return 1
                r = self.cmd_read_mem(ser,a1,len(flashdata))
                if not r[0]:
                    fout.write('Read back failed %s\n' % (r[1:],))
                    return 1
                dback = r[1]
                if dback != flashdata:
                    fout.write('Verify failed\n')
                    return 1

        self.reset(ser,bootloader=0)

        return

def main(argv):
    gp = STM32flash()
    try:
        opts, args = getopt.getopt(argv[1:],
                                   'b:r:w:ue:vn:g:s:fhcA:N:',
                                   ['verbose',
                                    'addr=',
                                    'npages=',
                                    'read=',
                                    'write=',
                                    ])
    except getopt.error, msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-b', '--speed'):
            gp.speed = int(arg)
        elif opt in ('-r', '--read'):
            gp.filename = arg
            gp.op = 'r'
        elif opt in ('-w', '--write'):
            gp.filename = arg
            gp.op = 'w'
        elif opt in ('-A', '--addr'):
            gp.addr = int(arg,0)
        elif opt in ('-N', '--npages'):
            gp.npages = int(arg,0)

    gp.doit(args)

if __name__ == '__main__':
    main(sys.argv)
