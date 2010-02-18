import time
import array
import struct
from datetime import date, time, datetime, timedelta

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

def read_time(val):
  return time(val/_MILLISECONDS_PER_HOUR,(val/_MILLISECONDS_PER_MINUTE)%60,(val/1000)%60,microsecond=1000*(val%1000))

def write_time(val):
  return _MILLISECONDS_PER_HOUR*val.hour + _MILLISECONDS_PER_MINUTE*val.minute + 1000*val.second + val.microsecond/1000

def read_date(val):
  return date.fromordinal(val + _Y2KDAYS)
  
def write_date(val):
  return val.toordinal() - _Y2KDAYS

def read_datetime(val):
  return timedelta(milliseconds=val*_MILLISECONDS_PER_DAY) + _Y2KDATETIME

def write_datetime(val):
  delta = val - _Y2KDATETIME
  return delta.days + (delta.seconds / _SECONDS_PER_DAY) + (delta.microseconds / _MICROSECONDS_PER_DAY)

# End Time Translation Stuff

def read_symbol(endianness,offset,bytes):
  end = bytes.find("\0",offset)
  return (bytes[offset:end],end+1)

def write_symbol(val,message):
  message.fromstring(val + struct.pack('b',0))
  return message

class q_str(str):
  def __new__(cls,s,is_char=False):
    if is_char: s = s[0]
    s=super(q_str,cls).__new__(cls,s)
    s.is_char=is_char
    return s

class TranslateType():
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

types = {}

types['bool'] = TranslateType(bool,1,'b',1)
types['byte'] = TranslateType(code=4,format='b',offset=1)
types['int'] = TranslateType(int,6,'i',4)
types['short'] = TranslateType(code=5,format='i',offset=2)
types['float'] = TranslateType(float,9,'d',8)
types['real'] = TranslateType(code=8,format='f',offset=4)
types['long'] = TranslateType(long,7,'q',8)
types['char'] = TranslateType(q_str,10,'c',1,additional_read=lambda x: q_str(x,True))
types['symbol'] = TranslateType(str,11,'b',None,overwrite_read=read_symbol,overwrite_write = write_symbol)
types['month'] = TranslateType(month,13,'i',4,additional_write=int,additional_read=month.from_int)
types['date'] = TranslateType(date,14,'i',4,additional_write=write_date,additional_read=read_date)
types['datetime'] = TranslateType(datetime,15,'d',8,additional_write=write_datetime,additional_read=read_datetime)
types['minute'] = TranslateType(minute,17,'i',4,additional_write=int,additional_read=minute.from_int)
types['second'] = TranslateType(second,18,'i',4,additional_write=int,additional_read=second.from_int)
types['time'] = TranslateType(time,19,'i',4,additional_write=write_time,additional_read=read_time)
