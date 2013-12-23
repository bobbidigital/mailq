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
        return self._readNextEntry()

    def nextMail(self):
        return self._readNextEntry()

    def _getRecordLength(self, recordLine):
        recordLength = 2
        try:
            statusIndicator = re.match(mailq.expressions['queueId'],
                                       recordLine).group(1)[-1]
            #TODO Never seen other statuses, so don't know  line lengths
            if statusIndicator in mailq.statusSymbols.values():
                recordLength = 1
            return recordLength
        except AttributeError:
            raise InvalidParameter(
                "Invalid Parameter Line must have QueueId present") 

    def _getRecord(self):
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


    def _readNextEntry(self):
        while True:
            entryString = self._getRecord()
            if not entryString:
               raise StopIteration()
            mailQRecord = self.createRecord(entryString)
            yield mailQRecord

    def createRecord(self, entryString):
        fields = {}
        for key, expression in mailq.expressions.iteritems():
            if key in ['toAddress']:
                fields[key] = re.findall(expression, entryString,
                    re.IGNORECASE | re.MULTILINE)
            else:
                try:
                    fields[key] = re.search(expression, entryString,
                        re.IGNORECASE | re.MULTILINE).group(1)
                except AttributeError:
                    fields[key] = '-'
        MailQRecord = namedtuple('MailQRecord', mailq.expressions.keys())
        return MailQRecord(**fields)


