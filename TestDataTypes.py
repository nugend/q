import unittest
import q

class TestDataTypes(unittest.TestCase):
    
    def setUp(self):
        self.conn = q.q('v-kdbd-01', 5003, 'mwarren')
    
    def testInteger(self):
        self.conn.k('test:2')
        self.assertEqual(self.conn.k('test'), 2)

    def testFloat(self):
        self.conn.k('test:2f')
        self.assertEqual(self.conn.k('test'), 2.0)
        
    def testMonth(self):
        self.conn.k('test:2008.09m')
        self.assertEqual(str(self.conn.k('test')), '2008-09')
        
    def testDate(self):
        self.conn.k('test:2008.09.09')
        self.assertEqual(str(self.conn.k('test')), '2008-09-09')
    
    def testDateTime(self):
        self.conn.k('test:2008.09.09T01:01:01.001')
        self.assertEqual(str(self.conn.k('test')), '2008-09-09 01:01:01.001000')
        
if __name__ == '__main__':
    unittest.main()
