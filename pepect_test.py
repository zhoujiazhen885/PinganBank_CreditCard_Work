#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pexpect

child = pexpect.spawn("ssh ftpuser@10.1.183.81 'ls ' " )
child.expect('password:')
child.sendline('ftpuser123')
