#
# Copyright (c) 2009 by Matt Warren
# 
# This file is part of qPy.
# 
# qPy is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# qPy is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General
# Public License for more details.
# 
# You should have received a copy of the GNU Lesser General
# Public License along with qPy; if not, write to the Free
# Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA  02111-1307  USA
# 

#
# Written by Matt Warren
#

import socket
import select
import array
import struct
import time
import datetime

SYNC=True
ASYNC=False
nt = [ 0, 1, 0, 0, 1, 2, 4, 8, 4, 8, 1, 0, 0, 4, 4, 8, 0, 4, 4, 4 ]  #byte length of different datatypes
 

class Month:
    def __init__(self, x):
        self.i = x
    def __str__(self):
        m = self.i + 24000
        y = m / 12
        return '%(decade)02d%(year)02d-%(month)02d' % {'decade': y/100, 'year': y % 100, 'month':(m+1)%12}
class Minute:
    def __init__(self, x):
        self.i = x
    def __str__(self):
        return '%(hour)02d:%(minute)02d' % {'hour': self.i/60, 'minute': self.i % 60}
class Second:
    def __init__(self, x):
        self.i = x
    def __str__(self):
        return '%(minute)s:%(second)02d' % {'minute': str(Minute(self.i/60)), 'second': self.i % 60}
class Dict:
    """Dict is a generalized dict.  It just contains the keys and values as two objects and provides a way to 
    interact with it."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.index = 0
    def __iter__(self):
        return self
    def next(self):
        if self.index > len(self.x)-1:
            raise StopIteration
        self.index += 1
        return self.x[self.index-1], self.y[self.index-1]
    def __str__(self):
        result = ""
        for i in range(0, len(self.x)):
            result += str(self.x[i]), str(self.y[i]) + "\n"
        return result
class Flip:
    """Flip is a different way to look at table data held in a Dict
    It assumes that the dictionary contains values which are equal length arrays"""
    def __init__(self, d):
        self.x = []  #column names
        self.y = []  #column data (stored by column)
        for k,v in d:
            self.x.append(k)
            self.y.append(v)
        self.length = len(self.y[0])
        self.index = 0
    def __len__(self):
        return self.length 
    def __iter__(self):
        return self
    def next(self):
        """Return the row"""
        if self.index > self.length-1:
            raise StopIteration
        row = []
        for v in self.y:
            row.append(v[self.index])
        self.index += 1
        return row
    def __str__(self):
        string = ""
        for row in self:
            string += str(row) + "\n"
        self.index = 0
        return string
    
def td(x):
    """A Dict containing two Flips is how keyed tables are encoded, td joins the 2 Dict objects into a single Flip object"""
    if isinstance(x, Flip): return x
    if not isinstance(x, Dict): raise Exception('This function takes a Dict type')
    a = x.x
    b = x.y
    m = len(a.x)
    n = len(b.x)
    x = []
    for item in a.x: x.append(item)
    for item in b.x: x.append(item)
    y = []
    for item in a.y: y.append(item)
    for item in b.y: y.append(item)
    return Flip(Dict(x,y))
          
          
k = 86400000L * 10957

      
class q:
    
    RECONNECT_ATTEMPTS = 5  # Number of reconnect attempts to make before throwing exception
    RECONNECT_WAIT = 5000 # Milliseconds to wait between reconnect attempts 
    MAX_MSG_QUERY_LENGTH = 1024 # Maximum number of characters from query to return in exception message
    MAX_MSG_LIST_LENGTH = 100 # Maximum length of a data list specified in a query before it is summarized in exception message
    
    
    # offset the long version of the date by the timezone
    def o(self, x):
        return x.timezone
    
    def lg(self, x):
        return x + self.o(x)
    
    def gl(self, x):
        return x - self.o(x - self.o(x))
        
    
    
    
    def wt(self, z):
        l = z.time()
        w( l == nj if nf else (lg(l) - k) / 8.64e7)
        
    
    #socket stuff starts here
    def io(sock):
        s = sock
        i = s
    
    def __init__(self, host, port, user):
        self.host=host
        self.port=port
        self.user=user
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()
  
  	def close(self):
  		self.sock.close()
  		
    def connect(self, attempts=1):
        if self.host=='' :
            raise Exception('bad host')
        for attempt in range(attempts):
            try:
                self.sock.connect((self.host,self.port))
                login = array.array('b')  #signed char array (bytes)
                login.fromstring(self.user)
                login.append(0) #null terminated string
                self.sock.send(login.tostring())
                result = self.sock.recv(1)  #blocking recv
                #print ':', result
                if not result:
                    raise Exception("access denied")
                
            except:
                raise Exception ('unable to connect to host')
        
    def ns(str):
        if str=='' or str==None:
            return 0
        else:
            return str.find('\000')
        
    def n(self, x):
        #return self.n(x.x) if isinstance(x, dict) else self.n(x.y[0]) if isinstance(x, flip) else len(x);
        return self.n(x.x) if isinstance(x, Dict) else len(x);
    
    def _nx(self, x):
        i = 0
        qtype = self._qtype(x)
        j = 6
        n = self.n(x)
        j += n * nt[qtype];
        return j;
    
    def _qtype(self, x):
        """Encode the type of x as an integer that is interpreted by q"""
        #TODO figure out how to deal with array types
        if isinstance(x, array.array):
            return 10 if x.typecode == 'c' else \
               10 if x.typecode == 'h' else \
				6 if x.typecode == 'i' else \
				7 if x.typecode == 'l' else \
				8 if x.typecode == 'f' else \
				8 if x.typecode == 'd' else \
				0
			
        return -1 if isinstance(x, bool) else \
        	-6 if isinstance(x, int) else \
			-8 if isinstance(x, float) else \
			-7 if isinstance(x, long) else \
			-11 if isinstance(x, str) else \
			-13 if isinstance(x, Month) else \
			-17 if isinstance(x, Minute) else \
			-18 if isinstance(x, Second) else \
			98 if isinstance(x, Dict) else \
			99 if isinstance(x, Flip) else \
			0
    
    def _write(x, message):
    	"""determine the type of x and write it to the binary message for output"""
    	t = _qtype(x)
    	message.fromstring(struct.pack('b', t))
    	
        def writeDict( x, y):
            _write(x)
            _write(y)
            
    	{-1: lambda: message.fromstring(struct.pack('b', x)),
    	-6: lambda: message.fromstring(struct.pack('>i', x)),
    	-8: lambda: message.fromstring(struct.pack('>f', x)),
    	-7: lambda: message.fromstring(struct.pack('>l', x)),
    	-11: lambda: message.fromstring(x),
    	-13: lambda: message.fromstring(struct.pack('>i', x.i)),
    	-17: lambda: message.fromstring(struct.pack('>i', x.i)),
    	-18: lambda: message.fromstring(struct.pack('>i', x.i)),
        -98: lambda: writeDict(x.x, x.y),
    	-99: lambda: message.fromstring(struct.pack('>i', x)),
    	}[t]()
    	
    def k(self, query):
        global SYNC
        if isinstance(query, str): self._send(SYNC, array.array('c',query))
        else: self._send(SYNC, query)
        return self._readFromServer()
        
    def _send(self, sync, query):
        n = self._nx(query) + 8
        if sync:
            message = array.array('b', [0,1,0,0]) # 1 for synchronous requests
        else:
            message = array.array('b', [0,0,0,0]) # 1 for synchronous requests
        message.fromstring(struct.pack('>i', n)) # n should be len(query)+14
        message.fromstring(struct.pack('i', 10)) # qtype of the data to follow
        message.fromstring(struct.pack('>h', len(query)))
        message.fromstring(query)
        self.sock.send(message)
       
    def _readFromServer(self):
        """read the response from the server"""
        header = self.sock.recv(8)
        little_endian = struct.unpack('b', header[0:1])[0] == 1  #byte order
        
        self.offset = 4
        dataSize = self._ri(little_endian, header)
        
        inputBytes = self.sock.recv(dataSize - 8)
        if struct.unpack_from('b', inputBytes, 0)[0] == -128 :
            self.offset = 1
            raise Exception(self._rs(little_endian, inputBytes))
        self.offset =0
        return self._r(little_endian, inputBytes)
    
    def _rb(self, little_endian, bytearray):
        """retrieve byte from bytearray at offset"""
        val = struct.unpack('b', bytearray[self.offset:self.offset+1])[0]
        self.offset+=1
        return val
    
    def _rc(self, little_endian, bytearray):
        """retrieve char from bytearray at offset"""
        val = struct.unpack('c', bytearray[self.offset:self.offset+1])[0]
        self.offset+=1
        return val
    
    def _ri(self, little_endian, bytearray):
        """retrieve integer from bytearray at offset"""
        val = struct.unpack('i' if little_endian else '>i', bytearray[self.offset:self.offset+4])[0]
        self.offset+=4
        return val
    
    def _rd(self, little_endian, bytearray):
        """retrieve integer from bytearray at offset"""
        val = struct.unpack('i' if little_endian else '>i', bytearray[self.offset:self.offset+4])[0]
        self.offset+=4
        return datetime.date.fromordinal(730120+val)  #730120 is the ordinal for 2000-01-01
     
    def _rt(self, little_endian, bytearray):
        """retrieve integer from bytearray at offset"""
        val = struct.unpack('d' if little_endian else '>d', bytearray[self.offset:self.offset+8])[0]
        self.offset+=8
        return datetime.datetime.fromtimestamp(946710000.0+(val*60*60*24))  #946710000 is the timestamp for 1999-12-31 23:00:00
        
    def _re(self, little_endian, bytearray):
        """retrieve float from bytearray at offset"""
        val = struct.unpack('f' if little_endian else '>f', bytearray[self.offset:self.offset+4])[0]
        self.offset+=4
        return val
    
    def _rj(self, little_endian, bytearray):
        """retrieve long from bytearray at offset"""
        val = struct.unpack('l' if little_endian else '>l', bytearray[self.offset:self.offset+8])[0]
        self.offset+=8
        return val
    
    def _rf(self, little_endian, bytearray):
        """retrieve double from bytearray at offset"""
        val = struct.unpack('d' if little_endian else '>d', bytearray[self.offset:self.offset+8])[0]
        self.offset+=8
        return val
    
    def _rh(self, little_endian, bytearray):
        """retrieve integer from bytearray at offset"""
        val = struct.unpack('h' if little_endian else '>h', bytearray[self.offset:self.offset+2])[0]
        self.offset+=2
        return val
    
    def _rs(self, little_endian, bytearray):
        """retrieve null terminated string from bytearray"""
        end = bytearray.find("\0",self.offset)
        val = bytearray[self.offset:end]
        self.offset = end+1
        return val
                   
    def _r(self, little_endian, bytearray):
        """General retrieve data from bytearray.  format is type number followed by data""" 
        t = self._rb(little_endian, bytearray)
        readType = {
            -1: lambda: self._rb(little_endian, bytearray),
            -4: lambda: self._rb(little_endian, bytearray),
            -5: lambda: self._rh(little_endian, bytearray),
            -6: lambda: self._ri(little_endian, bytearray),
            -7: lambda: self._rj(little_endian, bytearray),
            -8: lambda: self._re(little_endian, bytearray),
            -9: lambda: self._rf(little_endian, bytearray),
            -10: lambda: self._rc(little_endian, bytearray),
            -11: lambda: self._rs(little_endian, bytearray),
            -13: lambda: Month(self._ri(little_endian, bytearray)),
            -14: lambda: self._rd(little_endian, bytearray),
            -15: lambda: self._rt(little_endian, bytearray),
            -17: lambda: Minute(self._ri(little_endian, bytearray)),
            -18: lambda: Second(self._ri(little_endian, bytearray)),
            -19: lambda: self._ri(little_endian, bytearray),
            0: lambda: self._r(little_endian, bytearray),
            1: lambda: self._rb(little_endian, bytearray),
             4: lambda: self._rb(little_endian, bytearray),
             5: lambda: self._rh(little_endian, bytearray),
             6: lambda: self._ri(little_endian, bytearray),
             7: lambda: self._rj(little_endian, bytearray),
             8: lambda: self._re(little_endian, bytearray),
             9: lambda: self._rf(little_endian, bytearray),
             10: lambda: self._rc(little_endian, bytearray),
             11: lambda: self._rs(little_endian, bytearray),
             13: lambda: Month(self._ri(little_endian, bytearray)),
             14: lambda: self._ri(little_endian, bytearray),
             15: lambda: self._rf(little_endian, bytearray),
             17: lambda: Minute(self._ri(little_endian, bytearray)),
             18: lambda: Second(self._ri(little_endian, bytearray)),
             19: lambda: self._ri(little_endian, bytearray)
            }
        if t < 0 :
            #In this case the value is a scalar
            if readType.has_key(t) : return readType[t]()
        if t > 99 :
            if t == 100 :
                self._rs(little_endian, bytearray)
                return self._r(little_endian, bytearray)
            if t < 104 :
                return None if self._rb(little_endian, bytearray) == 0 and t == 101 else "func";
            self.offset = len(bytearray)
            return "func"
        
        if t == 99:
            keys = self._r(little_endian, bytearray)
            values = self._r(little_endian, bytearray)
            return Dict(keys, values)
        
        self.offset+=1;
        
        if t == 98:
            return Flip(self._r(little_endian, bytearray))
        
        n=self._ri(little_endian, bytearray) #length of the array
        val = []
        for i in range(0, n):
            item = readType[t]()
            val.append( item )
        return val
        
        return self._rs(little_endian, bytearray)

        
