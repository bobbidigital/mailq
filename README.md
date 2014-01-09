
#MailQ#

##Requirements##
Python 2.6 or Greater

##Intro##

MailQ is a parser for the Postfix and Sendmail mailq. It uses a generator, so you'll need to loop through the items line by line. The generator approach seemed safer considering
we have no idea how large the mailq might be. 


##Object Construction##

The MailQ object takes a file-lib object that contains the output of the mailq command. Due to various implementations and Python being cross-platform, the MailQReader object will not look for the mailq automatically. To supply a file-like object, the best approach is something like the following:
	
	import subprocess
	import StringIO
	output = subprocess.Popen(['/usr/bin/mailq'], stdout=subprocess.PIPE).stdout
	\#Then you'll want to convert that to a StringIO for file seek capabilities
	descriptor = StringIO.StringIO(output.read())


##Usage##

	from MailQReader import *
	
	mailq = MailQReader(mailQFileOutput)
	for item in mailq:
		\#Do stuff

##Properties Currently provided##

 
	* user - The username being sent to
	* fromAddress - who is sending the mail
	* toAddress - who is receiving the mail
	* domain - The domain of the toAddress
	* arrivalTime - When did the mail hit the queue (returned as a datetime object)
	* smtpCode - The SMTP Code provided by the log message (if applicable)
	* errorMessage - The error message provided by the SMTP server
	* queueId - The Queue ID

##Todo##

* Make this document a little better. 
* Get more log examples to flesh out edge cases
* Implement a count() function 
