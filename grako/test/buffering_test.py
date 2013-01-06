import os
import unittest
from ..buffering import Buffer

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.normpath(os.path.join(THISDIR, '../..'))

class BufferingTests(unittest.TestCase):

    def setUp(self):
        testfile = os.path.join(BASEDIR, 'etc/test_text')
        self.text = open(testfile).read()
        self.buf = Buffer(self.text, whitespace='')

    def test_pos_consistency(self):
        line = col = 0
        for p, c in enumerate(self.text):
            bl, bc, _ = self.buf.line_info(p)
            d = self.buf.next()
#            print 'tx', line, col, c.encode('string-escape')
#            print 'bu', bl, bc, d.encode('string-escape')
            self.assertEqual(bl, line)
            self.assertEqual(bc, col)
            self.assertEqual(d, c)
            if c == '\n':
                col = 0
                line += 1
            else:
                col += 1
    def test_next_consisntency(self):
        while not self.buf.atend():
            bl, bc, _ = self.buf.line_info()
#            print 'li', bl, bc
#            print 'bu', self.buf.line, self.buf.col
            self.assertEqual(bl, self.buf.line)
            self.assertEqual(bc, self.buf.col)
            self.buf.next()

def suite():
    pass

if __name__ == '__main__':
    unittest.main()
