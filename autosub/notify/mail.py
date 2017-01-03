import logging

import email.utils
import smtplib
from email.mime.text import MIMEText

import autosub

log = logging.getLogger('thelogger')

def _send_notify(message, mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth):
    if not mailsrv:
        mailsrv = autosub.MAILSRV
    
    if not mailfromaddr:
        mailfromaddr = autosub.MAILFROMADDR
    
    if not mailtoaddr:
        mailtoaddr = autosub.MAILTOADDR
    
    if not mailusername:
        mailusername = autosub.MAILUSERNAME
    
    if not mailpassword:
        mailpassword = autosub.MAILPASSWORD

    if not mailsubject:
        mailsubject = autosub.MAILSUBJECT
    
    if not mailencryption:
        mailencryption = autosub.MAILENCRYPTION
        
    if not mailauth:
        mailauth = autosub.MAILAUTH
            
    try:
        server = smtplib.SMTP(mailsrv)
        if mailencryption == u'TLS':
            server.starttls()
        if mailusername != '' and mailpassword != '':
            server.ehlo()
            if mailauth != u'':
                server.esmtp_features["auth"] = mailauth.upper()
            server.login(mailusername, mailpassword)
        server.sendmail(mailfromaddr, mailtoaddr, message)
        server.quit()
        log.info("Mail: Mail sent")
        return True
    except:
        log.error("Mail: Failed to send a mail")
        return False

def test_notify(mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth):
    log.debug("Mail: Trying to send a mail")
    message = MIMEText('Testing Mail settings from Auto-Sub.')
    message['From'] = email.utils.formataddr((mailfromaddr, mailfromaddr))
    message['To'] = email.utils.formataddr(('Recipient', mailtoaddr))
    message['Subject'] = 'Auto-Sub'
    message = message.as_string()
    return _send_notify(message, mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth)

def send_notify(lang, subtitlefile, videofile, website):
    log.debug("Mail: Trying to send a mail")
    message = MIMEText("""Hi,\n 
AutoSub downloaded the following subtitle\n\n
Language: %s\n 
File: %s\n
Videofile: %s\n
Website: %s\n
    """ %(lang, subtitlefile, videofile, website))
    message['From'] = email.utils.formataddr((autosub.MAILFROMADDR, autosub.MAILFROMADDR))
    message['To'] = email.utils.formataddr(('Recipient', autosub.MAILTOADDR))
    message['Subject'] = '%s %s' %(autosub.MAILSUBJECT, subtitlefile) 
    message = message.as_string()
    mailsrv = autosub.MAILSRV
    mailfromaddr = autosub.MAILFROMADDR
    mailtoaddr = autosub.MAILTOADDR
    mailusername = autosub.MAILUSERNAME
    mailpassword = autosub.MAILPASSWORD
    mailsubject = autosub.MAILSUBJECT
    mailencryption = autosub.MAILENCRYPTION
    mailauth = autosub.MAILAUTH
    return _send_notify(message, mailsrv, mailfromaddr, mailtoaddr, mailusername, mailpassword, mailsubject, mailencryption, mailauth)
    
