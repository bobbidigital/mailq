import unittest
import StringIO
import mailq
import datetime



class MailQTestCase(unittest.TestCase):


    def setUp(self):
        self.testFile = open('testdata.txt')
        self.fullTestFile = open('testdata_full.txt')
        self.redhatTestFile = open('testdata_rh.txt')
        self.recordAsDict = {'toAddress': 'bob@google.com',
                'fromAddress': 'orders@sender.com',
                'queueId': '6D8E95990244',
                'errorMessage': 'User is gone. 550 You mad bro?',
                'smtpCode': 550,
                'arrivalTime': 'Fri Dec 20 11:14:10'}



    def test_init(self):
        mailQ = mailq.MailQReader(self.testFile)
        self.testFile.seek(0)
        self.assertTrue(mailQ._queueData != None)
        i = 0
        for i, l in enumerate(mailQ._queueData):
            pass
        self.testFile.seek(0)
        self.assertEquals(i + 1, len(self.testFile.readlines()))
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
        for i in range(0,2):
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
        self.assertEquals(record.toAddress, 'ff@aim.com')
        self.assertEquals(record.smtpCode, '-')

    def test_fullFile(self):
        mailQ = mailq.MailQReader(self.fullTestFile)
        recordCount = []
        for entry in mailQ.nextMail():
            recordCount.append(entry)
        self.assertEquals(len(recordCount), 267)

    def test_redhatFile(self):
        mailQ = mailq.MailQReader(self.redhatTestFile)
        recordCount = []
        for entry in mailQ.nextMail():
            recordCount.append(entry)
        self.assertEquals(len(recordCount), 15)

    def test_domain(self):
        mailqItem = mailq.MailQRecord(**self.recordAsDict)
        self.assertEquals('google.com', mailqItem.domain)

    def test_user(self):
        mailqItem = mailq.MailQRecord(**self.recordAsDict)
        self.assertEquals('bob', mailqItem.user)


    def test_date_conversion(self):
        mailQ = mailq.MailQReader(self.redhatTestFile)
        dt = mailQ.convertDate(self.recordAsDict['arrivalTime'])
        convertedDate = datetime.datetime(2013, 12, 20, 11, 14, 10)
        self.assertEquals(dt, convertedDate)



if __name__ == '__main__':
    unittest.main()

