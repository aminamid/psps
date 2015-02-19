#!/bin/env python

import sys
import time
import imaplib
from logging import getLogger, basicConfig

logger = getLogger(__name__)
logcfg = {
  #"format": "%(asctime)s.%(msecs).03d %(process)d %(thread)x %(levelname).4s;%(module)s(%(lineno)d/%(funcName)s) %(message)s",
  "format": "%(asctime)s.%(msecs).03d %(message)s",
  "datefmt": "%Y/%m/%dT%H:%M:%S",
  "level": 15,
  "stream": sys.stderr,
}
basicConfig(**logcfg)


def get_parsed_opts():
    import optparse
    import os
    from logging import DEBUG,INFO
 
    opt = optparse.OptionParser()
    opt.add_option("-s", "--server", default='127.0.0.1' )
    opt.add_option("-p", "--port", default='143' )
    opt.add_option("-u", "--user", default='el00' )
    opt.add_option("-w", "--pswd", default='el00' )
    opt.add_option("-d", "--debug", default=0 )
    return opt.parse_args()

import hashlib

import imaplib
superclass=imaplib.IMAP4
excepts= (imaplib.IMAP4.error)

imaplib.Commands['XAPPLEPUSHSERVICE']= ('AUTH')

from random import randint
import re
class Client(superclass):
    def __init__(self, host = '', port = imaplib.IMAP4_PORT):
        self.debug = imaplib.Debug
        self.state = 'LOGOUT'
        self.literal = None             # A literal argument to a command
        self.tagged_commands = {}       # Tagged commands awaiting response
        self.untagged_responses = {}    # {typ: [data, ...], ...}
        self.continuation_response = '' # Last continuation response
        self.is_readonly = False        # READ-ONLY desired state
        self.tagnum = 0

        # Create unique tag for this session,
        # and compile tagged response matcher.


        self.tagpre = imaplib.Int2AP(randint(4096, 65535))
        self.tagre = re.compile(r'(?P<tag>'
                        + self.tagpre
                        + r'\d+) (?P<type>[A-Z]+) (?P<data>.*)')

        self.connect(host,port)

        typ, dat = self.capability()
        if dat == [None]:
            raise self.error('no CAPABILITY response from server')
        self.capabilities = tuple(dat[-1].upper().split())

        if __debug__:
            if self.debug >= 3:
                self._mesg('CAPABILITIES: %r' % (self.capabilities,))

        for version in imaplib.AllowedVersions:
            if not version in self.capabilities:
                continue
            self.PROTOCOL_VERSION = version
            return

        raise self.error('server not IMAP4 compliant')

    def connect(self, host, port):
        # Open socket to server.

        self.open(host, port)

        # Get server welcome message,
        # request and store CAPABILITY response.

        if __debug__:
            self._cmd_log_len = 10
            self._cmd_log_idx = 0
            self._cmd_log = {}           # Last `_cmd_log_len' interactions
            if self.debug >= 1:
                self._mesg('imaplib version %s' % __version__)
                self._mesg('new IMAP4 connection, tag=%s' % self.tagpre)

        self.welcome = self._get_response()
        if 'PREAUTH' in self.untagged_responses:
            self.state = 'AUTH'
            return 'OK', self.untagged_responses
        elif 'OK' in self.untagged_responses:
            self.state = 'NONAUTH'
            return 'OK', self.untagged_responses
        else:
            raise self.error(self.welcome)
            return 'NO', self.welcome

    def xapplepushservice(self, login_name, subtopic = "com.apple.mobilemail", mailboxes = ['INBOX'], dev_token = None, version = 2 ):
        name = 'XAPPLEPUSHSERVICE'
        if not dev_token:
            dev_token='{0}{0}'.format(hashlib.md5(login_name).hexdigest().upper())
        if version == 1:
          return self._simple_command(name,
            '"aps-version"', '"{0}"'.format(version),
            '"aps-account-id"', '"{0}"'.format(login_name),
            '"aps-device-token"', '"{0}"'.format(dev_token),
            '"aps-subtopic"', '"{0}"'.format(subtopic)
            )
        else:
          return self._simple_command(name,
            'aps-version', '{0}'.format(version),
            'aps-account-id', login_name,
            'aps-device-token', dev_token,
            'aps-subtopic', subtopic,
            'mailboxes', '({0})'.format(' '.join(mailboxes))
            )


def is_ok(result):
    return result[0] in ['OK', 'BYE']

target_func = [
    ('login',0),
    ('logout',0),
    ('select',0),
    ('fetch',0),
    ('close',0),
    ('getquota',0),
    ('expunge',0),
    ('lsub',0),
    ('list',0),
    ('search',0),
    ('capability',0),
    ('connect',0),
    ('xapplepushservice',0),
    ('uid',1),
]

psiterindex='imapserv'

def stat(modulename, method, is_ok, excepts, num_arg_show, psiter):

    def _wrapper(*args, **kwargs):
        subname = '-'.join([method.__name__] + [ x for x in args[1:num_arg_show+1] ])
        cmdarg  = ' '.join(['{0}'.format(x) for x in list(args[num_arg_show+1:]) if x])
        start_time = time.time()
        psiter.next()
        try:
            result = method(*args, **kwargs)
            psstr = ['{comm}: pid: {pid},  total: {cpu:.3f}, usr: {usr:.3f}, sys: {sys:.3f}, vsz: {vsz}, rsz: {rsz}'.format(**dict(v.items()+[('pid',k)])) for k,v in psiter.next().items() if isinstance( v, dict)  if 'comm' in v if psiterindex in v['comm'] ][0]
        except excepts as e:
            total_time = int((time.time() - start_time) * 1000)
            #logger.info("ER:{0}".format({'request_type':modulename, 'name':subname, 'response_time':total_time, 'exception':e}))
            logger.info("ER:{0:<10} {2:<24} {1:>10} ms,{3}:{4}".format(subname, total_time, cmdarg,psstr, e))
        else:
            if is_ok(result):
                total_time = int((time.time() - start_time) * 1000)
                logger.info("OK:{0:<10} {2:<24}: {1:>10} ms,{3}".format(subname, total_time, cmdarg,psstr))
                #logger.info("OK:{0}".format({'request_type':modulename, 'name':subname, 'response_time':total_time}))
                return result
            else:
                total_time = int((time.time() - start_time) * 1000)
                logger.info("NG:{0:<10} {2:<24}:{1:>10} ms, {3}".format(subname,  total_time, cmdarg,psstr))
                #logger.info("NG:{0}".format({'request_type':modulename, 'name':subname, 'response_time':total_time}))
                return result
    return _wrapper

from psmon import ProcInfoIter
itp=ProcInfoIter()
for cmd in target_func:
    setattr( Client, cmd[0],
        stat(
            modulename = superclass.__name__,
            method = getattr(Client, cmd[0]),
            is_ok = is_ok,
            excepts = excepts,
            num_arg_show = cmd[1],
            psiter=itp ) )

def main( flags, host, user, pswd, port=143, charset=None, count=1, debug=0 ):
    im = Client( host = host, port = port)
    im.debug=debug
    im.login( user, pswd)
    im.select('INBOX')
    for flag in flags:
      im.uid(*['SEARCH', charset]+flag.split(' '))
    im.logout()

if __name__ == '__main__':

    (opts, args) = get_parsed_opts()
    main(flags=args, host=opts.server, port=opts.port, user=opts.user, pswd=opts.pswd, debug=opts.debug)
