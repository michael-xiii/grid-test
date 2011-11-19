# -*- coding: utf-8 -*-
'''
Created on 02.08.2010

@author: michael
'''
import os
import procname

import twisted.web.server
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from src.libs.fast.core import FastServer, FastDbServer, FastConfigObject, FastObject
from src.libs.fast.fasttwisted import FastServerIndexResource

from src.libs.daemon import Daemon

from src.sshtunnel import resources
from subprocess import Popen

#==============================================================================
class SSHTunnelServer(FastServer, twisted.web.server.Site):
    logging      = True
    # own
    config_file  = 'sshtunneld'
    name         = 'SSH Tunnel Daemon'
    version      = '0.1'

    port         = 8080
    
    processes = {}
    tunnels = {}
    save_file = None
    
    #--------------------------------------------------------------------------
    def __init__(self):
        procname.setprocname(self.name)

        FastServer.__init__(self)
        
        #self._openLogFile(self._request_file)
        self.loadConfig()
    
        index = FastServerIndexResource(server=self)

        index.putChild('test', resources.TestResource(server=self))

        tunnel = FastServerIndexResource(server=self)
        index.putChild('tunnel' , tunnel)
        tunnel.putChild('start', resources.SSHTunnelStartJsonResource(server=self))
        tunnel.putChild('end', resources.SSHTunnelEndJsonResource(server=self))
        tunnel.putChild('check', resources.SSHTunnelCheckJsonResource(server=self))
        twisted.web.server.Site.__init__(self, index)
        

        lp = LoopingCall(self.checkTunnels)
        lp.start(1.0)
        self.save_file = os.path.join(self.dir, 'config', 'save.dat')  
        
        self.loadAllTunnels()
            

    #--------------------------------------------------------------------------
    def checkTunnels(self):
        #self._log('Looping call')
        pass        

    #--------------------------------------------------------------------------
    def saveAllTunnels(self):
        self._log('Save all tunnels')
        data = ''
        for port, tunnel in self.tunnels.items():
            self._log('%s' % tunnel)
            data += '%s|%s|%s|%s|%s\n' % (
                tunnel['local_port'],
                tunnel['remote_host'],
                tunnel['remote_port'],
                tunnel['firewall_user'],
                tunnel['firewall_host'],
            )
        with open(self.save_file, 'w') as f:
            f.write(data)

    #--------------------------------------------------------------------------
    def loadAllTunnels(self):
        self._log('Restoring all tunnels')
        try:
            with open(self.save_file, 'r') as f:
                data = f.read()
    
            for line in data.split('\n'):
                items = line.split('|')
                tunnel = {
                    'local_port' : items[0],
                    'remote_host' : items[1],
                    'remote_port' : items[2],
                    'firewall_user' : items[3],
                    'firewall_host' : items[4],
                }
                self.addTunnel(tunnel)
        except:
            self._error('Unable to restore tunnels')

    #--------------------------------------------------------------------------
    def addTunnel(self, tunnel):
        self._log('Add tunnel %s' % tunnel)
        local_port = tunnel['local_port']
        
        if local_port in self.processes:
            raise Exception('Port [%s] is already connected' % local_port)
        
        cmd = 'ssh -N -L %s:%s:%s %s@%s' % (                
                tunnel['local_port'],
                tunnel['remote_host'],
                tunnel['remote_port'],
                tunnel['firewall_user'],
                tunnel['firewall_host'],
            )
        p = Popen(cmd, shell=True)

        self.processes[local_port] = p 
        self.tunnels[local_port] = tunnel
        return cmd
        

    
#==============================================================================    
class SSHTunnelDaemon(Daemon):
    name   = 'sshtunneld'
    site   = None
    server = None
    
    #--------------------------------------------------------------------------
    def __init__(self):
        self.server = SSHTunnelServer()
        Daemon.__init__(self, pidfile='/var/run/%s-master.pid' % (self.name.lower()) )
        procname.setprocname(self.name)

    #--------------------------------------------------------------------------
    def run(self):
        self.server = SSHTunnelServer()
        reactor.listenTCP(self.server.port, self.server)
        reactor.run()
    
    #--------------------------------------------------------------------------   
    def reload(self):
        self.server = SSHTunnelServer()
        # @todo
        print 'Reloading - NIY'
        print self.server
        self.server.loadConfig()   


        

