import os
import unittest
from ..buffering import Buffer

THISDIR = os.path.dirname(os.path.abspath(__file__))
BASEDIR = os.path.normpath(os.path.join(THISDIR, '../..'))

class BufferingTests(unittest.TestCase):

    def test_buffering_pos(self):
        testfile = os.path.join(BASEDIR, 'etc/test_text')
        text = open(testfile).read()
        buf = Buffer(text, whitespace='')
        line = col = 0
        for p, c in enumerate(text):
            bp, bl, bc, _ = buf.line_info(p)
            d = buf.next()
#            print 'tx', p, line, col, c.encode('string-escape')
#            print 'bu', bp, bl, bc, d.encode('string-escape')
            self.assertEqual(bp, p)
            self.assertEqual(bl, line)
            self.assertEqual(bc, col)
            self.assertEqual(d, c)
            if c == '\n':
                col = 0
                line += 1
            else:
                col += 1

def suite():
    pass

if __name__ == '__main__':
    unittest.main()
