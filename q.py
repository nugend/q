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
import cStringIO
import itertools
from datetime import date, time, datetime, timedelta

#NOTE: Dealing with the impedance mismatch between Q symbols, chars and char lists and Python strings is a major pain-point
CHAR_CODE=10

class q_str(str):
  def __new__(cls,s,is_char=False):
    if is_char: s = s[0]
    s=super(q_str,cls).__new__(cls,s)
    s.is_char=is_char
    return s

class q_list(list):
  def __init__(self,l,code=None):
    super(q_list,self).__init__(l)
    if 0 == len(self):
      self.type=_code_dict[0]
    else:
      if code:
        self.type=_code_dict[code]
      elif isinstance(l,q_str):
        self.type=_code_dict[CHAR_CODE]
      else:
        self.type=self._determine_iter_type(l)

  @staticmethod
  def convert_sequence(val):
    if '__iter__' in dir(val) or '__getitem__' in dir(val) or (isinstance(val,q_str) and not val.is_char):
      return q_list(val)
    else:
      return val
  
  @staticmethod
  def _determine_iter_type(l,reeval=False):
    if (not reeval) and 'type' in dir(l):
      return l.type
    tc=map(lambda x:q_type(x).list_code,l)
    for code in tc[1:]:
      if tc[0] != code:
        return _types['list']
    return _code_dict[tc[0]]
  
  def _determine_type(self):
      self.type=self._determine_iter_type(self,True)

  def __getslice__(self,i,j):
    return q_list(super(q_list,self).__getslice__(i,j))
  
  @staticmethod
  def _add_list_helper(type,y):
    if type.list_code > 0 and q_list._determine_iter_type(y).code != type.code:
      return _types['list']
    else:
      return type

  def __setitem__(self,i,y):
    super(q_list,self).__setitem__(i,y)
    self.type = self._add_list_helper(self.type,[y])

  def __setslice__(self,i,j,y):
    super(q_list,self).__setslice__(i,j,y)
    self.type = self._add_list_helper(self.type,y)

  def __delitem__(self,y):
    super(q_list,self).__delitem__(y)
    self._determine_type()

  def __delslice__(self,i,y):
    super(q_list,self).__delslice__(i,y)
    self._determine_type()

  def __mul__(self,n):
    return q_list(super(q_list,self).__rmul__(n),code=self.type.code)

  def __rmul__(self,n): return self.__mul__(n)
  
  def __add__(self,y):
    if self.type.code == self._determine_iter_type(y):
      return q_list(super(q_list,self).__add__(y),code=self.type.code)
    else:
      return q_list(super(q_list,self).__add__(y))

  def __radd__(self,y): return self.__add__(y)
  def __iadd__(self,y): return self.__add__(y)

  def append(self,x):
    self[len(self):len(self)] = [x]

  def extend(self,x):
    self[len(self):len(self)] = x

  def insert(self,i,x):
    self[i:i] = [x]

  def pop(self,i=None):
    if i is None:
      i = len(self) - 1
    x = self[i]
    del self[i]
    return x

  def remove(self,x):
    del self[self.index(x)]

  @staticmethod
  def _write(val,message):
    return val._write_self(message)

  def _write_self(self,message):
    message.fromstring(_write_byte(0)+_write_integer(len(self)))
    for el in self: 
      if self.type.code != 0:
        message.fromstring(self.type.write_data(el))
      else:
        message.fromstring(q._write(el))
    return message

  @staticmethod
  def _read(reader,tcode,endianness,offset,bytes):
    (n, offset) = _read_integer(endianness,offset+1,bytes)
    val = q_list([])
    for i in range(0, n):
        (item,offset) = reader(endianness,offset,bytes)
        val.append(item)
    if tcode is CHAR_CODE:
      return (q_str(''.join(val)),offset)
    else:
      return (val,offset)

class flip(dict):

  @staticmethod
  def _read_flip(endianness,offset,bytes):
    (dictionary,offset) = q._read(endianness,offset+1,bytes)
    return (flip(dictionary),offset)

  @staticmethod
  def _write_flip(val,message):
    message.fromstring(_write_byte(0)+_write_byte(99))
    return _write_dict(message,val)


# Begin Time Translation Stuff

_Y2KDAYS = date(2000,1,1).toordinal()
_Y2KDATETIME = datetime(2000,1,1)

_MILLISECONDS_PER_HOUR = int(3.6e6)
_MILLISECONDS_PER_MINUTE = 60000
_MILLISECONDS_PER_DAY = int(8.64e7)

_SECONDS_PER_DAY = 86400.0
_MICROSECONDS_PER_DAY = _SECONDS_PER_DAY * 1e6

class month(date):
  @classmethod
  def from_int(cls,x):
    m = x + 24000
    return cls(m / 12,(m%12)+1,1)

  @classmethod
  def from_date(cls,x):
    return cls(x.year,x.month,1)

  def __int__(self):
    return (self.year * 12 + self.month - 1) - 24000

class minute(time):
  @classmethod
  def from_int(cls,x):
    return cls(x/60,x%60)

  @classmethod
  def from_time(cls,x):
    return cls(x.hour,x.minute)

  def __int__(self):
    return (self.hour * 60 + self.minute)

class second(time):
  @classmethod
  def from_int(cls,x):
    return cls(x/3600,(x/60)%60,x%60)
  
  @classmethod
  def from_time(cls,x):
    return cls(x.hour,x.minute,x.second)

  def __int__(self):
    return (self.hour * 3600 + self.minute * 60 + self.second)

def _read_time(val):
  return time(val/_MILLISECONDS_PER_HOUR,(val/_MILLISECONDS_PER_MINUTE)%60,(val/1000)%60,microsecond=1000*(val%1000))

def _write_time(val):
  return _MILLISECONDS_PER_HOUR*val.hour + _MILLISECONDS_PER_MINUTE*val.minute + 1000*val.second + val.microsecond/1000

def _read_date(val):
  return date.fromordinal(val + _Y2KDAYS)
  
def _write_date(val):
  return val.toordinal() - _Y2KDAYS

def _read_datetime(val):
  return timedelta(milliseconds=val*_MILLISECONDS_PER_DAY) + _Y2KDATETIME

def _write_datetime(val):
  delta = val - _Y2KDATETIME
  return delta.days + (delta.seconds / _SECONDS_PER_DAY) + (delta.microseconds / _MICROSECONDS_PER_DAY)

# End Time Translation Stuff

def _read_symbol(endianness,offset,bytes):
  end = bytes.find("\0",offset)
  return (bytes[offset:end],end+1)

def _write_symbol(val,message):
  message.fromstring(val + struct.pack('b',0))
  return message

def _read_dict(endianness,offset,bytes):
   (keys,offset) = q._read(endianness,offset,bytes)
   (values,offset) = q._read(endianness,offset,bytes)
   return (dict(itertools.izip(keys, values)),offset)

def _write_dict(val,message):
  return q._write(q_list(val.iterkeys()),q._write(q_list(val.itervalues()),message))

class _TranslateType():
  def __init__(self,type=type(None),code=-128,format='x',offset=1,additional_read=None,additional_write=None,overwrite_read=None,overwrite_write=None):
    self.type=type
    if code > 0 and code < 20:
      self.code=-code
    else:
      self.code=code
    self.list_code=code
    self.format=format
    self.offset=offset
    self.additional_read=additional_read
    self.additional_write=additional_write
    self.overwrite_read=overwrite_read
    self.overwrite_write=overwrite_write

  def read_data(self,endianness,offset,bytes):
    if self.overwrite_read:
      return self.overwrite_read(endianness,offset,bytes)
    else:
      val = struct.unpack(endianness(self.format),bytes[offset:offset+self.offset])[0]
      if self.additional_read:
        val = self.additional_read(val)
    return (val,offset+self.offset)
  
  def write_data(self,val,message=None):
    if message is None: message = array.array('b')
    if self.overwrite_write:
      return self.overwrite_write(val,message)
    else:
      if self.additional_write:
        val = self.additional_write(val)
      message.fromstring(struct.pack('>'+self.format,val))
      return message

_types = {}

_types['bool'] = _TranslateType(bool,1,'b',1)
_types['byte'] = _TranslateType(code=4,format='b',offset=1)
_types['int'] = _TranslateType(int,6,'i',4)
_types['short'] = _TranslateType(code=5,format='i',offset=2)
_types['float'] = _TranslateType(float,9,'d',8)
_types['real'] = _TranslateType(code=8,format='f',offset=4)
_types['long'] = _TranslateType(long,7,'q',8)
_types['char'] = _TranslateType(q_str,10,'c',1,additional_read=lambda x: q_str(x,True))
_types['symbol'] = _TranslateType(str,11,'b',None,overwrite_read=_read_symbol,overwrite_write = _write_symbol)
_types['month'] = _TranslateType(month,13,'i',4,additional_write=int,additional_read=month.from_int)
_types['date'] = _TranslateType(date,14,'i',4,additional_write=_write_date,additional_read=_read_date)
_types['datetime'] = _TranslateType(datetime,15,'d',8,additional_write=_write_datetime,additional_read=_read_datetime)
_types['minute'] = _TranslateType(minute,17,'i',4,additional_write=int,additional_read=minute.from_int)
_types['second'] = _TranslateType(second,18,'i',4,additional_write=int,additional_read=second.from_int)
_types['time'] = _TranslateType(time,19,'i',4,additional_write=_write_time,additional_read=_read_time)
_types['dict'] = _TranslateType(dict,99,overwrite_write=_write_dict,overwrite_read=_read_dict)
_types['flip'] = _TranslateType(flip,98,overwrite_write=flip._write_flip,overwrite_read=flip._read_flip)
_types['list'] = _TranslateType(q_list,0,overwrite_write=q_list._write,overwrite_read=q_list._read)

# Defines order of type code lookup (important for _types like q_str that are sub_types of a type already used for translation)
_type_order = ['char','symbol','month','date','minute','second','time','datetime','int','long','float','bool','real','short','byte','dict','flip'] 
_type_dict = dict(map(lambda x:(x.type,x),_types.itervalues()))      
_type_preferences = [(x.type,x) for x in map(_types.get,_type_order)]
_code_dict = dict(map(lambda x:(x.list_code,x),_types.itervalues()))
_read_byte = _types['byte'].read_data
_write_byte = _types['byte'].write_data
_read_integer = _types['int'].read_data
_write_integer = _types['int'].write_data
_read_symbol = _types['symbol'].read_data
_write_symbol = _types['symbol'].write_data
 

def q_type(x):
  if isinstance(x,list) or (isinstance(x,q_str) and not x.is_char): return _types['list']
  t = _type_dict.get(type(x))
  if t: return t
  for (inherited_type,t) in _type_preferences:
    if isinstance(x,inherited_type): return t
  return _TranslateType()
    
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
          
class q:
    
  SYNC=True
  ASYNC=False
  RECONNECT_ATTEMPTS = 5  # Number of reconnect attempts to make before throwing exception
  RECONNECT_WAIT = 5000 # Milliseconds to wait between reconnect attempts 
  MAX_MSG_QUERY_LENGTH = 1024 # Maximum number of characters from query to return in exception message
  MAX_MSG_LIST_LENGTH = 100 # Maximum length of a data list specified in a query before it is summarized in exception message

  def __init__(self, host='localhost', port=5000, user=''):
    self.host=host
    self.port=port
    self.user=user
    self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connect()
      
  def close(self):
    self.sock.close()
      
  def connect(self, attempts=1):
    # This for loop doesn't make sense, if there's an exception it'll just quit
    for attempt in range(attempts):
      try:
        self.sock.connect((self.host,self.port))
        login = array.array('b',self.user + '\0')  #null terminated signed char array (bytes)
        self.sock.send(login.tostring())
        result = self.sock.recv(1)  #blocking recv
        if not result:
          raise Exception("access denied")
      except:
        raise Exception ('unable to connect to host')
      
  def __call__(self, query, *args):
    if isinstance(query, str) and args is (): 
      self._send(q.SYNC, q_str(query))
    else:
      self._send(q.SYNC,[q_str(query)]+list(args))
    return self._receive()
      
  def _send(self, sync, query):
    if sync:
      message = array.array('b', [0,1,0,0]) # 1 for synchronous requests
    else:
      message = array.array('b', [0,0,0,0]) # 1 for synchronous requests
    message.fromstring(_write_integer(0)) # reserve space for message length
    message = self._write(query,message)
    message[4:8] = _write_integer(len(message))
    self.last_outgoing=message
    self.sock.send(message)

  @staticmethod
  def _write(val,message=None):
    if message is None: message = array.array('b')
    val = q_list.convert_sequence(val)
    t = q_type(val)
    if t.code is 0:
      t_code = val.type.list_code
    else:
      t_code = t.code
    message.fromstring(_write_byte(t_code))
    return t.write_data(val,message)

  def _receive(self):
    """read the response from the server"""
    header = self.sock.recv(8)
    #Endianness of byte doesn't matter when determining endianness
    endianness = lambda x:x
    if not _read_byte(endianness,0,header)[0] == 1:
      endianness = '>'.__add__
    (data_size,self.offset) = _read_integer(endianness,4,header)
    
    bytes = self._recv_size(data_size - 8)
    #ensure that it reads all the data
    if _read_byte(endianness,0,bytes)[0] == -128 :
      (val,self.offset) = _read_symbol(endianness,1,bytes)
      raise Exception(val)
    (val,self.offset) = self._read(endianness,0,bytes)
    return val
  
  def _recv_size(self, size):
    """read size bytes from the socket."""
    data=cStringIO.StringIO()
    recv_size=min(size,8192)
    while data.tell()<size:
      data.write(self.sock.recv(recv_size))
    v = data.getvalue()
    data.close()
    return v
  
  @staticmethod
  def _read(endianness,offset,bytes):
    (t,offset) = _read_byte(endianness,offset,bytes)
    if t < 0 or t == 98 or t == 99:
      return _code_dict[abs(t)].read_data(endianness,offset,bytes)
    elif t > 0 and t < 98:
      return q_list._read(_code_dict[t].read_data,t,endianness,offset,bytes)
    elif t is 0:
      return q_list._read(q._read,t,endianness,offset,bytes)
    else:
      (v,offset) = _read_byte(endianness,offset,bytes)
      if t == 101 and v == 0: return (None,offset)
      else: return ("func",len(bytes))
