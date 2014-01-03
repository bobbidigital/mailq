import re
import StringIO
import mailq
from collections import namedtuple

expressions = {'queueId': '^\s*([a-zA-Z0-9\*\-]+)',
               'fromAddress': '\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})',
               'toAddress': '^\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\n',
               'errorMessage': '^\s*\(([^\)]+)',
               'smtpCode': '^\s*\([^\)]+ ([4-5][0-9]{2})',
               }



statusSymbols = {'processing': '*', 'highLoad': 'X','tooYoung': '-'}

class InvalidParameter(Exception):
    pass


class MailQReader(object):

    _queueData = None
    _previousLine = ""

    def __init__(self, fd, hasHeader=True):
        try:
            fd.readline()
            if not hasHeader:
                fd.seek(0)
            self._queueData = fd
        except AttributeError:
            raise InvalidParameter('Method takes a file-like object')

    def __iter__(self):
        return self

    def __next__(self):
        return self.nexMail()

    def nextMail(self):
        # Use a generator because we don't know how big the mailq
        # will be. Safer to move through it record by record
        while True:
            entryString = self._getRecord()
            if not entryString or self.isEndOfFileMarker(entryString):
               raise StopIteration()
            else:
               mailQRecord = self.createRecord(entryString)
               yield mailQRecord

    def _getRecordLength(self, recordLine):
        # Record lenghts can vary based on type. Loop through and figure
        # and figure out how long the record is so we read the right
        # number of lines.

        recordLength = 2
        try:
            statusIndicator = re.match(mailq.expressions['queueId'],
                                       recordLine).group(1)[-1]
            #TODO Never seen other statuses, so don't know  line lengths
            if statusIndicator in mailq.statusSymbols.values():
                recordLength = 1
            return recordLength
        except AttributeError:
            if self.isEndOfFileMarker(recordLine):
                return 1
            raise InvalidParameter(
                "Invalid Parameter Line must have QueueId present")

    def _getRecord(self):
        # Grab the record as a string
        line = self._queueData.readline()
        if not line:
            return ''
        lines = []
        lines.append(self._previousLine)
        lines.append(line)
        for i in range(1, self._getRecordLength(line)):
            lines.append(self._queueData.readline())
        while True:
            line = self._queueData.readline()
            if re.match(mailq.expressions['toAddress'], line, flags=re.IGNORECASE):
                lines.append(line)
            else:
                if not line:
                    self._queueData.readline()
                else:
                    self._previousLine = line
                break
        return ''.join(lines)


    def isEndOfFileMarker(self, entryString):
        endOfFile = '-- [0-9]+ Kbytes in [0-9]+ Requests.'
        if re.search(endOfFile, entryString):
            return True
        else:
            return False

    def createRecord(self, entryString):
        fields = {}
        for key, expression in mailq.expressions.iteritems():
            try:
                fields[key] = re.search(expression, entryString,
                   re.IGNORECASE | re.MULTILINE).group(1)
            except AttributeError:
                fields[key] = '-'
        #MailQRecord = namedtuple('MailQRecord', mailq.expressions.keys())
        mailqrecord = MailQRecord(**fields)
        return MailQRecord(**fields)


class MailQRecord(object):

    __dict = {}
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            self.__dict[key] = value

    def __getattr__(self, name):
        try:
            return self.__dict[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    @property
    def domain(self):
        return self.toAddress.split('@', 2)[1]

    @property
    def user(self):
        return self.toAddress.split('@',2)[0]

