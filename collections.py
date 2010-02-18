import itertools
from parse import parser
from types import TranslateType, q_str

#NOTE: Dealing with the impedance mismatch between Q symbols, chars and char lists and Python strings is a major pain-point
CHAR_CODE=10

class q_list(list):
  def __init__(self,l,code=None):
    super(q_list,self).__init__(l)
    if 0 == len(self):
      self.type=parser.code_dict[0]
    else:
      if code:
        self.type=parser.code_dict[code]
      elif isinstance(l,q_str):
        self.type=parser.code_dict[CHAR_CODE]
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
    tc=map(lambda x:parser.type(x).list_code,l)
    for code in tc[1:]:
      if tc[0] != code:
        return parser.types['list']
    return parser.code_dict[tc[0]]
  
  def _determine_type(self):
      self.type=self._determine_iter_type(self,True)

  def __getslice__(self,i,j):
    return q_list(super(q_list,self).__getslice__(i,j))
  
  @staticmethod
  def _add_list_helper(type,y):
    if type.list_code > 0 and q_list._determine_iter_type(y).code != type.code:
      return parser.types['list']
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
    message.fromstring(parser.write_byte(0)+parser.write_integer(len(self)))
    for el in self: 
      if self.type.code != 0:
        message.fromstring(self.type.write_data(el))
      else:
        message.fromstring(parser.write(el))
    return message

  @staticmethod
  def _read(reader,tcode,endianness,offset,bytes):
    (n, offset) = parser.read_integer(endianness,offset+1,bytes)
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
    (dictionary,offset) = parser.read(endianness,offset+1,bytes)
    return (flip(dictionary),offset)

  @staticmethod
  def _write_flip(val,message):
    message.fromstring(parser.write_byte(0)+parser.write_byte(99))
    return _write_dict(message,val)
 
def _read_dict(endianness,offset,bytes):
   (keys,offset) = parser.read(endianness,offset,bytes)
   (values,offset) = parser.read(endianness,offset,bytes)
   return (dict(itertools.izip(keys, values)),offset)

def _write_dict(val,message):
  return parser.write(q_list(val.iterkeys()),parser.write(q_list(val.itervalues()),message))

parser.types['dict'] = TranslateType(dict,99,overwrite_write=_write_dict,overwrite_read=_read_dict)
parser.types['flip'] = TranslateType(flip,98,overwrite_write=flip._write_flip,overwrite_read=flip._read_flip)
parser.types['list'] = TranslateType(q_list,0,overwrite_write=q_list._write,overwrite_read=q_list._read)
