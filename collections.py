from itertools import izip
from parse import parser
from types import TranslateType, q_str
from UserDict import DictMixin

#NOTE: Dealing with the impedance mismatch between Q symbols, chars and char lists and Python strings is a major pain-point
CHAR_CODE=10

class q_list(list):
  def __init__(self,l=[],code=None):
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

class q_dict(DictMixin):
  def __init__(self,arg=None,**kwargs):
    self._keys=q_list()
    self._values=q_list()
    if getattr(arg,"keys",False) and getattr(arg,"values",False):
      self._keys.extend(arg.keys())
      self._values.extend(arg.values())
    elif getattr(arg,"iteritems",False):
      for (k,v) in arg.iteritems():
        self._keys.append(k)
        self._values.append(v)
    elif getattr(arg,"items",False):
      for (k,v) in arg.items():
        self._keys.append(k)
        self._values.append(v)
    elif arg:
      for (k,v) in arg:
        self._keys.append(k)
        self._values.append(v)
    else:
      self._keys.extend(kwargs.keys())
      self._values.extend(kwargs.values())

  def keys(self):
    return self._keys

  def values(self):
    return self._values

  def __getitem__(self,i):
    try:
      return self._values[self._keys.index(i)]
    except ValueError:
      raise KeyError(i)

  def __setitem__(self,i,y):
    try:
      self._values[self._keys.index(i)]=y
    except ValueError:
      self._keys.append(i)
      self._values.append(y)

  def __delitem__(self,i):
    try:
      p = self._keys.index(i)
      del self.keys[p]
      del self.keys[p]
    except ValueError:
      raise KeyError(i)

  def __contains__(self,i):
    return i in self._keys

  def __iter__(self):
    return iter(self._keys)

  def iteritems(self):
    return izip(iter(self._keys),iter(self._values))

  def __repr__(self):
    return "{" + ", ".join([repr(x)+": " + repr(y) for x in self._keys for y in self._values]) + "}"

  @staticmethod
  def _smallest_diff_key(a,b):
    return min([k for k in a if a.get(k) != b.get(k)])

  def __cmp__(self,other):
    if len(self) != len(other):
      return cmp(len(self),len(other))
    self_diff = _smallest_diff_key(self,other)
    other_diff = _smallest_diff_key(other,self)
    if self_diff != other_diff:
      return cmp(self_diff,other_diff)
    return cmp(self[self_diff],other[other_diff])
 
  @staticmethod
  def _read(endianness,offset,bytes):
    (keys,offset) = parser.read(endianness,offset,bytes)
    (values,offset) = parser.read(endianness,offset,bytes)
    dictionary=q_dict()
    dictionary._keys=keys
    dictionary._values=values
    if isinstance(keys,table) and isinstance(values,table):
      return (table(dictionary),offset)
    else:
      return (dictionary,offset)

  @staticmethod
  def _write(val,message):
    return parser.write(val.keys(),parser.write(val.values(),message))

class flip(q_dict):
  def __init__(self,val):
    self._storage=val

  @staticmethod
  def _read(endianness,offset,bytes):
    (dictionary,offset) = parser.read(endianness,offset+1,bytes)
    return (table(flip(dictionary)),offset)

  @staticmethod
  def _write(val,message):
    message.fromstring(parser.write_byte(0)+parser.write_byte(99))
    return q_dict._write(message,val._storage)

class table:
  def __init__(self,val):
    pass

  @staticmethod
  def _write(val,message):
    pass

parser.types['dict'] = TranslateType(dict,99,overwrite_write=q_dict._write,overwrite_read=q_dict._read)
parser.types['flip'] = TranslateType(flip,98,overwrite_write=flip._write,overwrite_read=flip._read)
parser.types['list'] = TranslateType(q_list,0,overwrite_write=q_list._write,overwrite_read=q_list._read)
parser.types['table'] = TranslateType(table,overwrite_write=table._write)
