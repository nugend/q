import array
from types import TranslateType, q_str, types

class Parser:
  def __init__(self,types):
    self.types=types
    # Defines order of type code lookup (important for types like q_str that are sub_types of a type already used for translation)
    self.type_order = ['char','symbol','month','date','minute','second','time','datetime','int','long','float','bool','real','short','byte','dict','flip','table']
  
  def update_types(self):
    self.read_byte = types['byte'].read_data
    self.write_byte = types['byte'].write_data
    self.read_integer = types['int'].read_data
    self.write_integer = types['int'].write_data
    self.read_symbol = types['symbol'].read_data
    self.write_symbol = types['symbol'].write_data

    self._type_dict = dict(map(lambda x:(x.type,x),self.types.itervalues()))      
    self._type_preferences = [(x.type,x) for x in map(self.types.get,self.type_order)]
    self.code_dict = dict(map(lambda x:(x.list_code,x),self.types.itervalues()))
    

  def type(self,x):
    if isinstance(x,list) or (isinstance(x,q_str) and not x.is_char): return self.types['list']
    if isinstance(x,self.types['table'].type):
      return self.type(x._data)
    t = self._type_dict.get(type(x))
    if t: return t
    for (inherited_type,t) in self._type_preferences:
      if isinstance(x,inherited_type): return t
    return TranslateType()

  def read(self,endianness,offset,bytes):
    (t,offset) = self.read_byte(endianness,offset,bytes)
    if t < 0 or t == 98 or t == 99:
      return self.code_dict[abs(t)].read_data(endianness,offset,bytes)
    elif t > 0 and t < 98:
      return self.types['list'].overwrite_read(self.code_dict[t].read_data,t,endianness,offset,bytes)
    elif t is 0:
      return self.types['list'].overwrite_read(self.read,t,endianness,offset,bytes)
    else:
      (v,offset) = self.read_byte(endianness,offset,bytes)
      if t == 101 and v == 0: return (None,offset)
      else: return ("func",len(bytes))

  def write(self,val,message=None):
    if message is None: message = array.array('b')
    val = self.types['list'].type.convert_sequence(val)
    t = self.type(val)
    if t.code is 0:
      t_code = val.type.list_code
    else:
      t_code = t.code
    message.fromstring(parser.write_byte(t_code))
    return t.write_data(val,message)

parser = Parser(types)
