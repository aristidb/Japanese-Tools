#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Christoph Dittmann <github@christoph-d.de>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# A very simple IRC bot providing a single interface for most of the
# Japanese tools.
# 

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import threading
import string
import random
import os, subprocess, sys

scripts = [('rtk', '../rtk/rtk'),
           ('romaji', '../romaji/romaji'),
           ('read', '../reading/read.py'),
           ('hira', '../kana/hira'),
           ('kata', '../kana/kata'),
           ('ja', '../jmdict/ja'),
           ('gt', '../google_translate/gt')
           ]

def run_script(path, argument, irc_source, irc_target):
    try:
        return subprocess.Popen(
            [path, argument],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(path)),
            env={ 'DMB_SENDER'   : irc_source,
                  'DMB_RECEIVER' : irc_target }
            ).communicate()[0]
    except:
        return 'An error occured.'

def limit_length(s, max_bytes):
    """Limits the length of a unicode string after conversion to
    utf-8. Returns a unicode string."""
    for limit in range(max_bytes, 0, -1):
        if len(s[:limit].encode('utf-8')) <= max_bytes:
            return s[:limit]
    return u''

class SimpleBot(SingleServerIRCBot):
    def __init__(self, channel, nickname, nickpass, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.nickpass = nickpass
        # magic_key is used for admin commands. E.g., "magic_key say
        # test" in a query with the bot triggers the admin command
        # "say".
        self.magic_key = ''.join([random.choice(string.ascii_letters) for x in range(8)]) + ' '
        self.print_magic_key()

    def print_magic_key(self):
        print 'Today\'s magic key for admin commands: %s' % self.magic_key,
        sys.stdout.flush()

    def debug_out(self, line):
        # Overwrite magic key.
        print '\r' + (100 * ' ') + '\r' + line
        # Print magic key again.
        self.print_magic_key()

    def say(self, lines, to=None):
        if to is None:
            to = self.say_target
        if isinstance(lines, str):
            try:
                lines = unicode(lines, 'utf-8')
            except ValueError:
                lines = unicode(lines, 'iso-8859-15')
        # Limit maximum number of lines and line length.
        for line in lines.splitlines()[:4]:
            self.connection.privmsg(to, limit_length(line, 410).encode('utf-8'))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + '_')

    def on_welcome(self, c, e):
        if self.nickpass is not None:
            self.connection.privmsg('NickServ', 'identify ' + self.nickpass)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.current_event = e
        self.say_target = nm_to_n(e.source())
        line = e.arguments()[0]
        self.do_command(line)
        self.debug_out('<%s> %s' % (e.source(), line))

    def on_pubmsg(self, c, e):
        self.current_event = e
        a = e.arguments()[0]
        if len(a) > 0 and a[0] == '!':
            self.say_target = e.target()
            self.do_command(a[1:])
        return

    def do_command(self, cmd):
        """This method will never raise an exception based on the
        Exception base class."""
        try:
            self.do_command_unsafe(cmd)
        except Exception, e:
            self.debug_out('Caught exception: %s' % str(e))

    def do_command_unsafe(self, cmd):
        """This method could raise an exception."""
        if cmd[0:len(self.magic_key)] == self.magic_key:
            self.do_special_command(cmd[len(self.magic_key):])
        else:
            self.do_user_command(cmd)

    def do_special_command(self, cmd):
        """Commands only the admin may use."""
        cmd = cmd.split(' ', 1)
        if cmd[0] == 'die':
            if len(cmd) == 1:
                self.die(u'さようなら'.encode('utf-8'))
            else:
                self.die(cmd[1])
        elif cmd[0] == 'say':
            self.say(cmd[1], self.channel)
        elif cmd[0] == 'privmsg':
            cmd = cmd[1].split(' ', 1)
            self.connection.privmsg(cmd[0], cmd[1])
        else:
            self.say('Unknown command.')

    def do_user_command(self, cmd):
        """Commands normal users may use."""
        if cmd == 'version':
            self.say(u'A very simple bot with 日本語 support.')
            return
        cmd = cmd.split(' ', 1)
        e = self.current_event
        for s in scripts:
            if s[0] == cmd[0]:
                self.say(run_script(s[1], cmd[1], nm_to_n(e.source()), e.target()))

def main():
    import sys
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print 'Usage: bot.py <server[:port]> <channel> <nickname> [NickServ password]'
        sys.exit(1)

    s = sys.argv[1].split(':', 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print 'Error: Invalid port.'
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]
    nickpass = None
    if len(sys.argv) == 5:
        nickpass = sys.argv[4]

    bot = SimpleBot(channel, nickname, nickpass, server, port)
    try:
        bot.start()
    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, exiting...'
        bot.do_special_command('die')
        bot.start()

if __name__ == '__main__':
    main()
