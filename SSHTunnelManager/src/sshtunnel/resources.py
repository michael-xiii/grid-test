# -*- coding: utf-8 -*-
'''
Created on 02.08.2010

@author: michael
'''
from src.libs.fast.fasttwisted import FastServerResource, FastJsonServerResourceDeferred
from subprocess import Popen

#==============================================================================   
class SSHTunnelStartJsonResource(FastJsonServerResourceDeferred):
    logging = True
    
    #--------------------------------------------------------------------------
    def _getData(self, request):
        '''
        Ставим задачу на установку тоннеля
        @todo - потеряем процесс если нет ключа
        '''
        params = request.args
        local_port = params['local_port'][0]
        tunnel =  {
                'local_port' : local_port,
                'remote_host' : params['remote_host'][0],
                'remote_port' : params['remote_port'][0],
                'firewall_user' : params['firewall_user'][0],
                'firewall_host' : params['firewall_host'][0],
            }
        
        cmd = self._server.addTunnel(tunnel)
        self._server.saveAllTunnels()
        
        return {'cmd'  : cmd, 'pid' : self._server.processes[local_port].pid}

#==============================================================================   
class SSHTunnelEndJsonResource(FastJsonServerResourceDeferred):
    logging = True
    #--------------------------------------------------------------------------
    def _getData(self, request):
        '''
        @todo errors
        '''
        params = request.args
        
        local_port = params['local_port'][0]

        if local_port in self._server.processes:
            #self._server.processes[local_port].terminate()
            p = self._server.processes[local_port]
            p.kill()
            cmd = 'kill %s' % p.pid
            # @todo check result
            Popen(cmd, shell=True)
            

        if local_port in self._server.tunnels:
            del self._server.tunnels[local_port]

        return {'result' : 1}

#==============================================================================   
class SSHTunnelCheckJsonResource(FastJsonServerResourceDeferred):
    logging = True
    #--------------------------------------------------------------------------
    def _getData(self, request):
        return {'result' : 1}
             
#==============================================================================   
class TestResource(FastServerResource):
    '''
    Base class for test form
    '''
    # twisted
    isLeaf = True    
    allowedMethods = ('GET',)

    #--------------------------------------------------------------------------
    def render(self, request):
        '''
        List of rules
        '''
        response  = '''
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                </head>
            <body>
                <form action="/tunnel/start" method="post">
                    <h3>Start:</h3>
                    Local port: <input name="local_port" type="text" value="32400"/><br/>
                    Remote host: <input name="remote_host" type="text" value="scaleclub.org"/><br/>
                    Remote port: <input name="remote_port" type="text" value="80"/><br/>
                    Firewall user: <input name="firewall_user" type="text" value="__backup"/><br/>
                    Firewall host: <input name="firewall_host" type="text" value="scalemodels.ru"/><br/>
                    Firewall pass: <input name="firewall_password" type="text" value="%&8aSdg5aJoeW5"/><br/>
                    <input type="submit">
                </form>
                <form action="/tunnel/end" method="post">
                    <h3>End:</h3>
                    Local port: <input name="local_port" type="text" value="32400"/><br/>
                    <input type="submit">
                </form>
                
                <hr>

            </body></html>''' 

        return response
 
