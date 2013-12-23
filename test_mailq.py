import unittest
import StringIO
import mailq



class MailQTestCase(unittest.TestCase):


    def setUp(self):
        self.testFile = open('testdata.txt')



    def test_init(self):
        mailQ = mailq.MailQReader(self.testFile)
        self.assertTrue(mailQ._queueData != None)
        i = 0
        for i, l in enumerate(mailQ._queueData):
            pass
        self.assertEquals(i + 1, 26)
        self.assertRaises(mailq.InvalidParameter, mailq.MailQReader, 'Bobby')


    def test_iteration(self):

        test_values = ['878005990241*', '6D8E95990244*', 'F2DE9599011D', 'F0EFA5990191',
            'F30283C88316', 'F28DF5990081', 'F0CF559901F0']
        test_values.reverse()
        mailQ = mailq.MailQReader(self.testFile)
        for entry in mailQ.nextMail():
            test_value = test_values.pop()
            self.assertEquals(test_value, entry.queueId)


    def test_getRecordLength(self):
        text = '878005990241*    3448 Fri Dec 20 11:14:10  frank@example.com'
        mailQ = mailq.MailQReader(self.testFile)
        lineCount = mailQ._getRecordLength(text)
        self.assertEquals(lineCount, 1)
        text = ' F2DE9599011D    14094 Thu Dec 19 22:27:40  frank@example.com'
        lineCount = mailQ._getRecordLength(text)
        self.assertEquals(lineCount, 2)

    def readTestRecord(self):
        f = open('testdata.txt')
        f.readline()
        lines = []
        for i in range(0,3):
            lines.append(f.readline())
        return ''.join(lines)

    def test_getRecord(self):
        mailQ = mailq.MailQReader(self.testFile)
        record = mailQ._getRecord()
        self.assertEquals(self.readTestRecord(), record)

    def test_createRecord(self):
        mailQ = mailq.MailQReader(self.testFile)
        record = mailQ.createRecord(self.readTestRecord())
        self.assertEquals(record.queueId, '878005990241*')
        self.assertEquals(record.fromAddress, 'frank@example.com')
        self.assertEquals(record.toAddress, ['ff@aim.com',
            'jeff@frank.com'])
        self.assertEquals(record.smtpCode, '-')



if __name__ == '__main__':
    unittest.main()

