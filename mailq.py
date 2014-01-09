import re
import mailq
import sys
import datetime

expressions = {'queueId': '^\s*([a-zA-Z0-9\*\-]+)',
               'fromAddress': '\s*<?([A-Z0-9._%+-]+@[A-Z0-9._-]+\.[A-Z]{2,4})>?',
               'toAddress': '^\s*<?([A-Z0-9._%+-]+@[A-Z0-9._-]+\.[A-Z]{2,4})>?\n',
               'errorMessage': '^\s*\(([^\)]+)',
               'smtpCode': '^\s*\([^\)]+ ([4-5][0-9]{2})',
               'arrivalTime':
               '([A-Z]{3}\s[A-Z]{3}\s+[0-9]{1,2}\s[0-9]{2}:[0-9]{2}:?[0-9]{0,2})'
               }

footer_types =  ['-- [0-9]+ Kbytes in [0-9]+ Requests.',
                    '\s*Total requests: [0-9]+']

header_types = ['\s+.+mqueue \([0-9]+ requests\)',
                '^-+Q-ID-+\s', '^-Queue ID-']
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
            raise InvalidParameter('Constructor takes a file-like object')

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
        # out how long the record is so we read the right
        # number of lines. This maybe refactored now that I understand the
        # mailq file format a bit more

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

        #Skip blank linkes, but make sure we're not at EOF
        while not line.strip() and not len(line) == 0:
            line = self._queueData.readline()
        if len(line) == 0:
            raise StopIteration
        lines = []
        lines.append(line)
        for i in range(1, self._getRecordLength(line)):
            lines.append(self._queueData.readline())

        #It appeared like some older versions of mailq logs had multiple
        #recipients. Not sure if that still holds water, but just in case .
        #Another target for refactoring as I understand the logs better

        while True:
            line = self._queueData.readline()
            if re.match(mailq.expressions['toAddress'], line, flags=re.IGNORECASE):
                lines.append(line)
            else:
                self._queueData.seek(len(line) * -1, 1)
                break
        return ''.join(lines)


    def isEndOfFileMarker(self, entryString):

        for footer in mailq.footer_types:
            if re.search(footer, entryString):
                return True
        return False

    def isHeader(self, line):
        for header in mailq.header_types:
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
        fields['arrivalTime'] = self.convertDate(fields['arrivalTime'])
        mailqrecord = MailQRecord(**fields)
        return MailQRecord(**fields)

    def convertDate(self, dateString):
        # The year isn't logged, so we'll assume it's this year. But end of
        # year stuff might be weird, so check and see if date is in the future.
        # If it is, assume last year
        dateStringWithYear = "%s %s" % (dateString, datetime.datetime.today().year)
        dt = self.getDateObject(dateStringWithYear)
        if dt > datetime.datetime.today():
            dateStringWithYear = "%s %s" % (dateString,
                datetime.datetime.today().year - 1)
            dt = self.getDateObject(dateStringWithYear)
        return dt

    def getDateObject(self, dateString):
        try:
            return datetime.datetime.strptime(dateString, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            return datetime.datetime.strptime(dateString, "%a %b %d %H:%M %Y")


class MailQRecord(object):

    __dict = {}
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            self.__dict[key] = value

    # Override getattr so that we can dynamically create properties 
    # for parsed properties. Still will need to create a property method
    # if you need to do anything but just return the value

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

