#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("/usr/share/pyshared")

import pickle
from datetime import datetime

import twisted.web
#import twisted.python.log
import twisted.web.resource

from twisted.internet import defer                                                                                                                              
from twisted.web import server                                                                                                                                  
from twisted.internet import reactor                                                                                                                            
from twisted.python import failure 


try:
    import json
except:
# @todo - don't understood what happens with remarked code
    import simplejson as json

from core import FastObject, getMD5Hash

is_array = lambda var: isinstance(var, (list, tuple))

#===============================================================================
class FastServerResource(FastObject, twisted.web.resource.Resource):
    '''
    Base class for any web resource used in Mobi Servers
    '''
    def __init__(self, server):
        FastObject.__init__(self)
        twisted.web.resource.Resource.__init__(self)
        self.bindServer(server)
        
    #---------------------------------------------------------------------------
    def bindServer(self, server):
        '''
        Bind resourse to some server
        '''       
        if server is None:
            self._log('Achtung')
        else:
            self._server = server        


        
        
#==============================================================================
class FastServerIndexResource(FastServerResource):
    '''
    Base class for JSON resource used in Mobi Servers
    '''    
    # twisted
    isLeaf = False    
    allowedMethods = ('GET', 'POST')
    
    
#==============================================================================
class FastJsonServerResource(FastServerResource):
    '''
    Base class for JSON resource used in Mobi Servers
    '''    
    # twisted
    isLeaf = True    
    allowedMethods = ('GET', 'POST')

    _isHtml = False
    _htmlHeader  = '''<html><head>
        <meta http-equiv="Content-Type" 
            content="text/response; charset=utf-8" />
        </head><body>'''
    _errorsArray = {
        'ERROR_PARAM_MISSED': 'Missed required param [%s]',
        'ERROR_PARAM_SHORT' : 
            'Search query param [%s] too short - minimum length is [%s]',
        'ERROR_INTERNAL'    : 'Unable to process request [%s]'        
    }
    #logging = True

    #--------------------------------------------------------------------------
    def checkHtmlMode(self, request):
        '''
        Check page is need HTML mode and check connection
        '''
        #self._server.checkDbConnection(self._server._db)
        if request.args.has_key('html'):
            if request.args['html'] == '1':
                self._isHtml = True
        
    #--------------------------------------------------------------------------
    def returnJsonResponse(self, request, data):
        '''
        Return JSON/HTML request  
        '''
        if self._isHtml:
            response  = self._htmlHeader + self._toHtml(request, data) 
        else:
            # @todo Twisted 8.1 backporting - for 10.0 enable this
            type = 'text/javascript; charset=UTF-8'
            request.responseHeaders.setRawHeaders('Content-Type', [type,])
            
            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime) else None

            response = json.dumps(data, ensure_ascii=False, default=dthandler)
            
        return response

    
    #--------------------------------------------------------------------------
    def _toHtml(self, request, dataself):
        '''
        Need to redefine in childs
        '''
        raise
    
    
    #--------------------------------------------------------------------------
    def getParam(self, request, name, default=0):  
        '''
        Return request parameter for first key
        '''     
        if request.args.has_key(name):
            #print name+'='+request.args[name][0]
            if is_array(request.args[name]):
                return request.args[name][0].strip()
            else:
                return request.args[name].strip()
        else:
            return default

    #--------------------------------------------------------------------------
    def getParamsSet(self, request, names):
        data = {}
        for name in names:
            data[name] = self.getParam(request, name, 0)
        return data


    #--------------------------------------------------------------------------
    def getParamLength(self, string):  
        '''
        Return param length using UTF-8 > cp866 conversion (in SYMBOLS)
        '''     
        return len(unicode(string, 'utf-8').encode("cp866"))

    
    #--------------------------------------------------------------------------
    def getJsonError(self, request, type, args):
        msg = self._errorsArray[type] % args
        self._error('JSON Error [%s] [%s]' % (type, msg))
        return self.returnJsonResponse(request, {'errors' : 
                ({'type' : type, 'text' : msg} )})
        
        
    #--------------------------------------------------------------------------
    def getMissedParamResponse(self, request, name):  
        '''
        Show response when requires param is missed
        '''
        return self.getJsonError(request, 'ERROR_PARAM_MISSED', (name,))


    #--------------------------------------------------------------------------
    def getQueryShortResponse(self, request, name):  
        '''
        Show response when search query too short
        '''
        return self.getJsonError(request, 'ERROR_PARAM_SHORT', 
                                 (name, self._server.min_query_length,))
    
    
    #--------------------------------------------------------------------------
    def exceptionToJson(self, request, ex):
        '''
        Process exception
        '''
        return self.getJsonError(request, 'ERROR_INTERNAL', (ex,))
    
#============================================================================== 
try:
    import memcache
  
    class FastJsonMemcacheServerResource(FastJsonServerResource):
        mc = None
        isLeaf = True    
    
        #--------------------------------------------------------------------------
        def initMemcache(self):
            memserver = self._server.config.get('memcache', 'server')
            
            self._log('Try connect to memcache [%s]' % memserver)
            self.mc = memcache.Client( [ memserver ], debug=1)
    
            if not self.mc:
                raise Exception('Unable to connect to memcache at [%s]' % memserver)
            
            self._log('Enabling Memcache [%s]' % self.mc)
except:
    pass
        
        
#==============================================================================   
class FastJsonServerResourceDeferred(FastJsonServerResource):
    logging = True

    #--------------------------------------------------------------------------
    def render(self, request):
        '''
        Отображаем запрос
        '''
        try:
            deferred  = defer.Deferred()                                                                                                                        

            args = {'request' : request, 'deferred' : deferred}                                                                                
            deferred.addCallback(self.successCbk, args)                                                                                                         
            deferred.addErrback(self.errorCbk, args)                                                                                                         

            reactor.callLater(0, self._deferredHandler, args)                                                                                                            
            return server.NOT_DONE_YET
                
        except Exception, ex:                                                                                                                                   
            return self.exceptionToJson(request, ex)
        
    #--------------------------------------------------------------------------
    def _deferredHandler(self, args):
        '''
        Обёртка для вызова deferred 
        '''
        try:
            request  = args['request']                                                                                                                              
            deferred = args['deferred']

            data = self._getData(request)
        
            deferred.callback(self.returnJsonResponse(request, data))
        except Exception, ex:
            #deferred.errback(self.exceptionToJson(request, ex))         
            deferred.errback( ex )         
  
    #--------------------------------------------------------------------------
    def _getData(self, request):
        '''
        Сохраняем полученные данные
        '''
        raise Exception('Method _handleRendering should be redefined!')
            
    #--------------------------------------------------------------------------                                                                                 
    def successCbk(self, page, args):                                                                                                                           
        '''                                                                                                                                                     
        Callback for operator detection                                                                                                                         
        '''                                                                                                                                                     
        request  = args['request']                                                                                                                              
        request.write(page) #args                                                                                                                               
        request.finish()
        
    #--------------------------------------------------------------------------                                                                                 
    def errorCbk(self, failure, args):                                                                                                                          
        '''                                                                                                                                                     
        Errback for error in operator detection http                                                                                                            
        '''                                                                                                                                                     
        request  = args['request']                                                                                                                              
        request.write(self.exceptionToJson(request, failure.getErrorMessage()))                                                                                                                                 
        request.finish()                    

        
        

