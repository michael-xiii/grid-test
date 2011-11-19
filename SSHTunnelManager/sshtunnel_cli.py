#!/usr/bin/python
# -*- coding: utf-8 -*-
# This is console server - for daemon please use sshtunneld
'''
Created on 14.11.2011                                                                                            

@author: michael
'''
from twisted.internet import reactor
import src.sshtunnel.server

try:
    server = src.sshtunnel.server.SSHTunnelServer()
    reactor.listenTCP(server.port, server)
    reactor.run()
except Exception, ex:
    print 'Unable to start SSH Tunnel Server:', ex


