# -*- coding: utf-8 -*
import logging
from .sage_email import default_email_address
from .smtpsend import send_mail
from socket import getfqdn

logger = logging.getLogger('notification')


class TwistedEmailHandler(logging.Handler):
    """Sends log messages via SMTP using a running twisted reactor."""
    def __init__(self, conf, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.conf = conf
        self.setFormatter(
            logging.Formatter('''
Host:               %(fqdn)s
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s

'''))

    def emit(self, record):
        fqdn = getfqdn()
        from_address = default_email_address()
        subject = '[sage-notebook] %s' % fqdn
        record.fqdn = fqdn
        message = self.format(record)

        recipients = self.conf['notification_recipients']
        if recipients is None:
            recipients = []
        for rcpt in recipients:
            to = rcpt.strip()
            send_mail(from_address, to, subject, message)
