import re
import mailq
import sys

expressions = {'queueId': '^\s*([a-zA-Z0-9\*\-]+)',
               'fromAddress': '\s*<?([A-Z0-9._%+-]+@[A-Z0-9._-]+\.[A-Z]{2,4})>?',
               'toAddress': '^\s*<?([A-Z0-9._%+-]+@[A-Z0-9._-]+\.[A-Z]{2,4})>?\n',
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
        charsRead = 0
        try:
            line = fd.readline()
            if not hasHeader:
                fd.seek(0)
            else:
                while self.isHeader(line):
                   line = fd.readline()
                   charsRead = len(line)
                fd.seek(charsRead * - 1, 1)
            self._queueData = fd
        except AttributeError:
            raise InvalidParameter('Method takes a file-like object')

    def __iter__(self):
        return self.__next__()

    def __next__(self):
        return self.nextMail()

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
        while not line.strip() and not len(line) == 0:
            line = self._queueData.readline()
        if len(line) == 0:
            raise StopIteration
        lines = []
        lines.append(line)
        for i in range(1, self._getRecordLength(line)):
            lines.append(self._queueData.readline())
        while True:
            line = self._queueData.readline()
            if re.match(mailq.expressions['toAddress'], line, flags=re.IGNORECASE):
                lines.append(line)
            else:
                self._queueData.seek(len(line) * -1, 1)
                break
        return ''.join(lines)


    def isEndOfFileMarker(self, entryString):
        footer_types =  ['-- [0-9]+ Kbytes in [0-9]+ Requests.',
                '\s*Total requests: [0-9]+']

        for footer in footer_types:
            if re.search(footer, entryString):
                return True
        return False

    def isHeader(self, line):
        header_types = ['\s+.+mqueue \([0-9]+ requests\)',
                '^-+Q-ID-+\s', '^-Queue ID-']
        for header in header_types:
            if re.match(header, line):
                return True
        return False

    def createRecord(self, entryString):
        fields = {}
        for key, expression in mailq.expressions.iteritems():
            try:
                fields[key] = re.search(expression, entryString,
                   re.IGNORECASE | re.MULTILINE).group(1)
            except AttributeError:
                fields[key] = '-'
        fields['raw'] = entryString
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
        try:
            return self.toAddress.split('@', 2)[1]
        except IndexError:
            return "-"

    @property
    def user(self):
        return self.toAddress.split('@',2)[0]

