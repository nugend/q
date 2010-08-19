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
import cStringIO

from types import q_str
from parse import parser as _parser

_parser.update_types()

class conn:
    
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
    message.fromstring(_parser.write_integer(0)) # reserve space for message length
    message = _parser.write(query,message)
    message[4:8] = _parser.write_integer(len(message))
    self.last_outgoing=message
    self.sock.send(message)

  def _receive(self):
    """read the response from the server"""
    header = self.sock.recv(8)
    #Endianness of byte doesn't matter when determining endianness
    endianness = lambda x:x
    if not _parser.read_byte(endianness,0,header)[0] == 1:
      endianness = '>'.__add__
    (data_size,self.offset) = _parser.read_integer(endianness,4,header)
    
    bytes = self._recv_size(data_size - 8)
    #ensure that it reads all the data
    if _parser.read_byte(endianness,0,bytes)[0] == -128 :
      (val,self.offset) = _parser.read_symbol(endianness,1,bytes)
      raise Exception(val)
    (val,self.offset) = _parser.read(endianness,0,bytes)
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
  
