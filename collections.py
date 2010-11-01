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
      if self.type.code == 0:
        self = _recurse_collections(self)

  @staticmethod
  def convert_sequence(val):
    if isinstance(val,q_str) and not val.is_char:
      return q_list(val)
    elif (not (isinstance(val,str) or isinstance(val,q_list) or isinstance(val,q_dict) or isinstance(val,table))) and ('__iter__' in dir(val) or '__getitem__' in dir(val)):
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
    super(q_list,self).__setitem__(i,_recurse_collections(y))
    self.type = self._add_list_helper(self.type,[y])

  def __setslice__(self,i,j,y):
    super(q_list,self).__setslice__(i,j,_recurse_collections(y))
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
      return q_list(super(q_list,self).__add__(_recurse_collections(y)),code=self.type.code)
    else:
      return q_list(super(q_list,self).__add__(_recurse_collections(y)))

  def __radd__(self,y): return self.__add__(y)
  def __iadd__(self,y): return self.__add__(y)

  def append(self,x):
    self[len(self):len(self)] = [_recurse_collections(x)]

  def extend(self,x):
    self[len(self):len(self)] = _recurse_collections(x)

  def insert(self,i,x):
    self[i:i] = [_recurse_collections(x)]

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
      val._determine_type()
      return (val,offset)

class q_dict(object,DictMixin):
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
    return list(self._keys)

  def values(self):
    return list(self._values)

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
    return "{" + ", ".join([repr(self._keys[x])+": " + repr(self._values[x]) for x in xrange(0,len(self._keys))]) + "}"

  @staticmethod
  def _smallest_diff_key(a,b):
    return min([k for k in a if a.get(k) != b.get(k)])

  def __cmp__(self,other):
    if len(self) != len(other):
      return cmp(len(self),len(other))
    self_diff = self._smallest_diff_key(self,other)
    other_diff = self._smallest_diff_key(other,self)
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
    if isinstance(val,table):
      return parser.write(val._data._values,parser.write(val._data._keys,message))
    return parser.write(val.values(),parser.write(val.keys(),message))

class flip(q_dict):

  @staticmethod
  def _read(endianness,offset,bytes):
    (dictionary,offset) = parser.read(endianness,offset+1,bytes)
    return (table(flip(dictionary)),offset)

  @staticmethod
  def _write(val,message):
    if isinstance(val,table):
      val=val._data
    message.fromstring(parser.write_byte(0)+parser.write_byte(99))
    return q_dict._write(val,message)

class table(object):
  def __init__(self,val,keys=[]):
    if isinstance(val,flip):
      self._data=val
      self._type=flip
    elif (isinstance(val,q_dict) and isinstance(val._keys,table) and isinstance(val._values,table)):
      self._data=val
      self._type=q_dict
    elif 0 < len(keys):
      self._data = q_dict()
      self._data._keys = table(izip(keys,[val[x] for x in keys]))
      non_keys = list(set(val.keys()).difference(keys))
      self._data._values = table(izip(non_keys,[val[x] for x in non_keys]))
      self._type=q_dict
    else:
      self._data=flip(val)
      self._type=flip

  def __eq__(self,other):
    if sorted(self.cols()) != sorted(other.cols()):
      return False
    if len(self) != len(other):
      return False
    for col in self.cols:
      if self[col] != other[col]:
        return False
    return True

  def __ne__(self,other):
    return not self == other

  def __len__(self):
    if self._type==flip:
      return len(self[self.cols()[0]])
    else:
      return len(self._data._keys)

  def cols(self):
    if self._type==flip:
      return self._data.keys()
    else:
      return self._data._keys.cols() + self._data._values.cols()

  def keys(self):
    if self._type==flip:
      raise ValueError
    else:
      return self._data._keys

  def values(self):
    if self._type==flip:
      raise ValueError
    else:
      return self._data._values

  @staticmethod
  def _validate_row(val,row):
    kfunc = getattr(row,"cols",getattr(row,"keys",False))
    if kfunc:
      return sorted(val.cols()) == sorted(kfunc())
    if len(val.cols()) > 1:
      if len(val.cols()) != len(row):
        return False
    else:
      if getattr(row,"__len__",False):
        return False
    return True

  def __getitem__(self,key):
    if self._type==flip:
      if isinstance(key,int):
        return q_dict(izip(self.cols(),[self._data[c][key] for c in self.cols()]))
      elif isinstance(key,slice):
        return table(flip(q_dict(izip(self.cols(),[self._data[c][key] for c in self.cols()]))))
      else:
        return self._data[key]
    else:
      if not self._validate_row(self.keys(),key):
        raise KeyError
      return self._data._values[self._data._keys.index(key)]

  def __setitem__(self,key,value):
    if self._type==flip:
      if isinstance(key,int) or isinstance(key,slice):
        if not self._validate_row(self,value):
          raise ValueError
        kfunc = getattr(value,"cols",getattr(value,"keys",False))
        if kfunc:
          for vk in kfunc():
            self._data[vk][key] = value[vk]
        else:
          for i, vk in enumerate(self.cols()):
            self._data[vk][key] = value[i]
      else:
        if len(value) != len(self._data[key]):
          raise ValueError
        self._data[key] = value
    else:
      if not self._validate_row(self.keys(),key):
        raise KeyError
      self._data._values[self._data._keys.index(key)] = value

  def __delitem__(self,key):
    if self._type==flip:
      if isinstance(key,int) or isinstance(key,slice):
        for c in self.cols():
          del self._data[c][key]
      else:
        del self._data[key]
    else:
      if not self._validate_row(self.keys(),key):
        raise KeyError
      del self._data._values[self._data._keys.index(key)]
      del self._data._keys[self._data._keys.index(key)]

  def index(self,val,start=0,stop=None,raise_miss=True):
    if getattr(val,"keys",False):
      cols = val.keys()
    elif not getattr(val,"__len__",False):
      cols = [self.cols()[0]]
      val = dict([(cols[0],val)])
    else:
      cols = self.cols()[0:len(val)]
      val = dict(izip(cols,val))
    for i in xrange(start,stop or len(self)):
      row = self[i]
      match = True
      for col in cols:
        if row[col] != val[col]:
          match = False
      if match:
        return i
    if raise_miss:
      raise ValueError
    else:
      return None

  def __iter__(self):
    if self._type == flip:
      for i in xrange(0,len(self)):
        yield self[i]
    else:
      for i in xrange(0,len(self._data._values)):
        yield self._data._values[i]

  def __contains__(self,item):
    if self._type == flip:
      return None != self.index(item,raise_miss=False)
    else:
      if not self._validate_row(self.keys(),item):
        raise KeyError
      return None != self._data._keys.index(item,raise_miss=False)

def _unknown_collection(x):
  return '__iter__' in dir(x) and not (isinstance(x,q_list) or isinstance(x,q_dict) or isinstance(x,table))

def _recurse_collections(c):
  if not _unknown_collection(c):
    return c
  if isinstance(c,dict):
    return q_dict(c)
  elif isinstance(c,list):
    for (i,e) in enumerate(c):
      if _unknown_collection(e):
        c[i] = _recurse_collections(e)
    return q_list(c)
  else:
    raise ValueError("Unknown collection type: " + str(type(c)))

parser.types['dict'] = TranslateType(q_dict,99,overwrite_write=q_dict._write,overwrite_read=q_dict._read)
parser.types['flip'] = TranslateType(flip,98,overwrite_write=flip._write,overwrite_read=flip._read)
parser.types['list'] = TranslateType(q_list,0,overwrite_write=q_list._write,overwrite_read=q_list._read)
parser.types['table'] = TranslateType(table)
