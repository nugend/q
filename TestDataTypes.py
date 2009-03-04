import unittest
import q
import datetime
import array
import cPickle

class TestDataTypes(unittest.TestCase):
    
    def setUp(self):
        self.conn = q.q('v-kdbd-01', 5003, 'mwarren')
    
    def testInteger(self):
        self.conn.k('{[x]test::x}', (15,))
        self.assertEqual(self.conn.k('test'), 15)
        self.conn.k('test:2')
        self.assertEqual(self.conn.k('test'), 2)

    def testFloat(self):
        self.conn.k('{[x]test::x}', (15.,))
        self.assertEqual(self.conn.k('test'), 15.)
        self.conn.k('test:2f')
        self.assertEqual(self.conn.k('test'), 2.0)
        
    def testMonth(self):
        self.conn.k('{[x]test::x}', (q.Month(1),))
        self.assertEqual(self.conn.k('test').i, q.Month(1).i)
        self.conn.k('test:2008.09m')
        self.assertEqual(str(self.conn.k('test')), '2008-09')
        
    def testSecond(self):
        self.conn.k('{[x]test::x}', (q.Second(61),))
        self.assertEqual(self.conn.k('test').i, q.Second(61).i)
        self.conn.k('test:00:01:01')
        self.assertEqual(str(self.conn.k('test')), '00:01:01')
        self.assertEqual(self.conn.k('test'), q.Second(61))
    
    def testMinute(self):
        self.conn.k('{[x]test::x}', (q.Minute(61),))
        self.assertEqual(self.conn.k('test').i, q.Minute(61).i)
        self.conn.k('test:01:01')
        self.assertEqual(str(self.conn.k('test')), '01:01')
        self.assertEqual(self.conn.k('test'), q.Minute(61))
        
    def testDate(self):
        now = datetime.datetime.now().date()
        self.conn.k('{[x;y]test::y}', [0,now])
        self.assertEqual(self.conn.k('test'), now)
        self.conn.k('test:2008.09.09')
        self.assertEqual(str(self.conn.k('test')), '2008-09-09')
        self.conn.k('test:1908.09.09')
        self.assertEqual(str(self.conn.k('test')), '1908-09-09')
    
    def testDateTime(self):
        now = datetime.datetime.now()
        self.conn.k('{[x]test::x}', (now,))
        self.assertEqual(self.conn.k('test'), now)
        self.conn.k('{[x;y]test::y}', [0,now])
        self.assertEqual(self.conn.k('test'), now)
        self.conn.k('test:2008.09.09T01:01:01.001')
        self.assertEqual(str(self.conn.k('test')), '2008-09-09 01:01:01.001000')
        self.conn.k('test:1999.09.09T01:01:01.001')
        self.assertEqual(str(self.conn.k('test')), '1999-09-09 01:01:01.001000')
        self.conn.k('test:1908.09.13T01:01:01.005')
        self.assertEqual(str(self.conn.k('test')), '1908-09-13 01:01:01.005000')
      
    def testTime(self):
        now = datetime.datetime.now().time()
        self.conn.k('{[x]test::x}', (now,))
        self.assertEqual(self.conn.k('test'), now)
        self.conn.k('test:01:01:01.001')
        self.assertEqual(str(self.conn.k('test')), '01:01:01.001000')
        self.conn.k('test:15:30:15.001')
        self.assertEqual(str(self.conn.k('test')), '15:30:15.001000')
        
    def testString(self):
        string = 'teststring'
        self.conn.k('{[x]test::x}', (string,))
        self.assertEqual(self.conn.k('test'), string)
        self.conn.k('test:`$"'+string+'"')
        self.assertEqual(str(self.conn.k('test')), string)
        
    def testChar(self):
        string = ['t','e']
        self.conn.k('{[x]test::x}', (string,))
        self.assertEqual(self.conn.k('test'), string)
        self.conn.k('test:"'+"".join(string)+'"')
        self.assertEqual(self.conn.k('test'), string)
        string = 't'
        self.conn.k('{[x]test::x}', (string,))
        self.assertEqual(self.conn.k('test'), string)
        self.conn.k('test:"'+"".join(string)+'"')
        self.assertEqual(self.conn.k('test'), string)
        
    def testBlob(self):
        dict = {'hello': 'world'}
        self.conn.k('test:`$"'+cPickle.dumps(dict)+'"')
        self.assertEqual(cPickle.loads(self.conn.k('test')), dict)
        
    def testDict(self):
        self.conn.k('test:(enlist `key)!(enlist `value)')
        t = self.conn.k('test')
        x = ['key',]
        y = ['value',]
        dict = q.Dict(x, y)
        self.conn.k('{[x]test::x}', (dict,))
        t = self.conn.k('test')
        self.assertEqual(self.conn.k('test'), dict)
        
    def tearDown(self):
        self.conn.close()
          
if __name__ == '__main__':
    unittest.main()
