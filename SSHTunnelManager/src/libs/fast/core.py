#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 25.01.2011

@author: michael_xiii
'''
import platform

import time
import os, sys
#import logging
#import logging.handlers

import ConfigParser, os, sys, MySQLdb, MySQLdb.cursors
import hashlib
from func import method_exists

from twisted.python.logfile import DailyLogFile
from twisted.python import log

import logging
import logging.handlers

CURRENT_PATH = os.path.realpath(os.path.dirname(__file__))

LOG_DIR = os.path.join(CURRENT_PATH, '../../../logs')
#@todo нормальное имя лога
LOG_FILE = os.path.join(LOG_DIR, 'monitord.log')

FILTERNAME='twistedfilter'
from syslog import syslog, openlog, LOG_MAIL

def trace_dump():
    t,v,tb = sys.exc_info()
    openlog(FILTERNAME, 0, LOG_MAIL)
    syslog('Unhandled exception: %s - %s' % (v, t))
    while tb:
        syslog('Trace: %s:%s %s' % (tb.tb_frame.f_code.co_filename,tb.tb_frame.f_code.co_name,tb.tb_lineno))
        tb = tb.tb_next
    # just to be safe
    del tb

def generate_password(passwordLength=10):
    '''
    Генерируем пароль пользователя
    нет 1 I 0 O - одинаковое начертание
    '''
    from random import Random
    rng = Random()
    righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
    lefthand = '789yuiophjknmYUIPHJKLNM'
    allchars = righthand + lefthand
    password = ''
    while len(password) < passwordLength:
        password = password + rng.choice(allchars)
    
    return password


#==============================================================================
def _functionId(nFramesUp):
    '''
    Create a string naming the function n frames up on the stack.
    '''
    co = sys._getframe(nFramesUp+1).f_code
    return "%s (%s @ %d)" % (co.co_name, co.co_filename, co.co_firstlineno)

#==============================================================================
def hashToString(args):
    string = ''
    for key in sorted(args.keys()):
        if key != 'self':
            string += key + '=' + str(args[key]).lower().replace(' ', '_') + '---'
    return string

#==============================================================================
def toupleToString(args):
    string = ''
    for value in args:
        string += str(value).lower().replace(' ', '_') + '---'
    return string
    

#==============================================================================
def getCacheKey(function, args):
    '''
    Translate arguments array to unique key
    '''
    string = function.__name__ + '---'+hashToString(args)
    return string  

#==============================================================================        
def getMD5Hash(textToHash=None):
    '''
    Получаем MD5 от строчки
    '''
    return hashlib.md5(textToHash).hexdigest()



#==============================================================================
class Log():
    """Logging class"""
    __fname = 0
    __pname = ''
    _log = None
    
    logging_twisted = True

    #--------------------------------------------------------------------------
    def __init__(self, pname='fastbilling', logname=LOG_FILE, loglevel=logging.DEBUG):
        # создатим папку, если не существует
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
        
        self.__fname = open(logname, 'a')
        self.__pname = pname
        FORMAT = ('%(asctime)-15s %(levelname)s %(message)s')
        
        if self.logging_twisted:
            #from twisted.application.service import Application
            #application = Application("foo")
            #(maxRotatedFiles=1)
            logging.basicConfig(format=FORMAT, filename=logname, handler=logging.handlers.RotatingFileHandler)
            observer = log.PythonLoggingObserver(loggerName='twisted')
            observer.start()
            observer.logger.setLevel(loglevel)

            #log.startLogging(DailyLogFile.fromFullPath(logname))
        else:
            self.__fname = open(logname, 'a')
            logging.basicConfig(format=FORMAT, filename=logname, handler=logging.handlers.RotatingFileHandler)
            self._log = logging.getLogger(self.__pname)
            self._log.setLevel(loglevel)
        
        
        

    #--------------------------------------------------------------------------
    def ustr(self, string):
        """Convert any string to <str> type"""
        #string = string.encode('utf-8')
        if type(string).__name__ == 'unicode':
#            value = string.decode('utf-8').encode('cp866')
            value = string.encode('cp866')
        else:
            value = string
        return value

    #--------------------------------------------------------------------------
    def __write(self, msg, logLevel):
        """Writing data to file"""
        log.msg(msg, logLevel=logLevel)

    #--------------------------------------------------------------------------
    def Error(self, msg):
        """Error log level"""
        if self.logging_twisted:
            self.__write(msg, logging.ERROR)
        else:
            logging.error(msg)

    #--------------------------------------------------------------------------
    def Warn(self, msg):
        """Warning log level"""
        self.__write(msg, logging.WARNING)

    #--------------------------------------------------------------------------
    def Info(self, msg):
        """Info log level"""
        if self.logging_twisted:
            self.__write(msg, logging.INFO)
        else:
            self._log.info(msg)

    #--------------------------------------------------------------------------
    def ExtInfo(self, msg):
        """ExtInfo log level"""
        if self.logging_twisted:
            self.__write(msg, logging.INFO)
        else:
            self._log.info(msg)

    #--------------------------------------------------------------------------
    def Note(self, msg):
        """ExtInfo log level"""
        if self.logging_twisted:
            self.__write(msg, logging.INFO)
        else:
            self._log.info("\033[1;34m" + msg)
            
    #--------------------------------------------------------------------------
    def Debug(self, msg):
        """Debug log level"""
        if self.logging_twisted:
            self.__write(msg, logging.DEBUG)
        else:
            self._log.debug(msg)

# @todo сделать конфиг для уровня логгирования
logger = Log()




#==============================================================================
class FastObject:
    '''
    Basic object with message and error log 
    '''
    logging = False
    data    = {}
    
    #--------------------------------------------------------------------------
    def __init__(self):
        self.logger = logger
    
    #--------------------------------------------------------------------------
    def _log(self, string, args=None):
        '''
        Logging messages of object level
        '''
        if self.logging:
            msg = ' %s : %s' %  (self.__class__.__name__, string)
            if args:
                msg = '%s [%s]' % (msg, args)
            self.logger.Debug(msg)
    
    #--------------------------------------------------------------------------
    def _error(self, string, args=None):
        '''
        Logging error of object level - log always
        @todo save to another file
        '''
        msg = ' %s : %s' % (self.__class__.__name__, string)
        if args:
            msg = '%s [%s]' % (msg, args)
        self.logger.Error(msg)

    #--------------------------------------------------------------------------
    def getHTML(self):
        '''
        Return HTML code for show SMS
        '''
        str = ''
        for key in self.data:
            str += '%s => %s<br/>' % (key, self.data[key])
        
        return str        
        
        
#==============================================================================
class FastDbObject(FastObject):
    _db       = False
    _cursor   = False
    _encoding = 'utf8'
    
    #--------------------------------------------------------------------------
    def __init__(self, db=None):
        FastObject.__init__(self)
        if db:
            self._db = db;
            self._cursor = self._db.cursor()
            

    #--------------------------------------------------------------------------
    def _query(self, sql, args = None):
        '''
        One query with commit
        '''
        result = self._cursor.execute(sql, args)
        self._db.commit()
        return result
    
    #--------------------------------------------------------------------------
    def _connectToDb(self):
        '''
        Try to connect to database using config
        '''
        try:
            self._cursor = self._db.cursor()

            self._log('Connected to DB :', self._db)
            if self._db == False:
                raise
        except Exception, ex:
            self._error('Unable connect to database', (ex, ex.args))    

    
    #--------------------------------------------------------------------------
    def checkDbConnection(self, db=None):
        '''
        Check connection and try to reconnect if it is broken
        '''
        try:
            if not db:
                db = self._db
            self.cursor = db.cursor()
            #cursor.execute('SET NAMES '+self._encoding+';')
        except Exception, e:
            self._log('Re-connect to database', (e, e.args))
            self._connectToDb()
                

#==============================================================================
class FastConfigObject(FastObject):
    dir         = '..'
    config_file = 'config'
    log_file    = 'log.log'
    config      = None
    
    #--------------------------------------------------------------------------
    def __init__(self, dir=None):
        FastObject.__init__(self)
        if dir:
            self.dir = dir
        else:
            co            = sys._getframe(0).f_code
            #@todo человеческий каталог
            path          = os.path.dirname(os.path.realpath(co.co_filename))+'/../../..'
            self.dir      = os.path.normpath( path )
        
        self.log_file = os.path.join(self.dir, 'logs', '%s.log' % self.config_file)

        # @todo Bug - UTF-8 string in log leads to exceptions
        #logging.basicConfig(filename=self.log_file, level=logging.DEBUG)


    #---------------------------------------------------------------------------
    def _readConfig(self, name):
        '''
        Read and parse config files
        '''
        try:
            config = ConfigParser.ConfigParser()
            
            default_config = name+'-defaults.ini'

            file = os.path.join(self.dir, 'config', default_config)
            self._log('Loading config [%s]...' % file)
            config.readfp(open(file))
            
            file1 = os.path.join(self.dir, 'config', name+'.ini')
            file2 = os.path.expanduser(os.path.join('~', '.%s.ini' % name))
            
            self._log('Loading configs [%s] [%s]...' % (file1, file2))
            
            config.read([file1, file2])
        except Exception, ex:
            self._error('Unable read any config file [%s.ini]' % name, (ex, ex.args))
            raise
        
        return config
    
    #--------------------------------------------------------------------------
    def loadConfig(self):
        '''
        Load config - using for 'reload' option from daemon
        '''
        try:
            new_config = self._validatedConfig()
            self._log('Apply config...')
            self.config = new_config
            
            if method_exists(self, '_connectToDb'):
                self._connectToDb()
            
            self.port = self.config.getint('daemon'  , 'port') 
            #self.gearman_server = self.config.get('main'  , 'gearman_server') 

            if method_exists(self, 'initMemcache'):
                self.initMemcache()
             
        except Exception, ex:
            self._error('Unable to load config: ', (ex,))
            if self.config is None:
                raise Exception('Unable to start - missed config [%s]' % ex)
            else:
                self._error('Unable to validate config - using old one [%s]' % ex)            
            raise
    
    
    #--------------------------------------------------------------------------
    def _validatedConfig(self):
        '''
        Load and validate config 
        '''
        self._log('Loading config...')
        config   = self._readConfig(self.config_file)
        self._log('Validating config...')

        return config
        
#==============================================================================
class FastServer(FastConfigObject):
    '''
    Class for web server
    '''
    # mobi
    logging      = True
    config_file  = None
    name         = None
    version      = None
    _user_agent  = None
    
    
    def __del__(self):
        pass

    #--------------------------------------------------------------------------
    def getUserAgent(self):
        '''
        Get user agent string for requests
        '''
        if self._user_agent is None:
            data = (self.name, self.version, 
                    platform.system(), platform.release())
            self._user_agent = '%s %s (%s %s)' % data 
        return self._user_agent
    

#==============================================================================
class FastDbServer(FastServer, FastDbObject):
    #--------------------------------------------------------------------------
    def _connectToDb(self):
        '''
        Try to connect to database using config
        '''
        try:
            self._db = MySQLdb.Connect(
                                   db     = self.config.get('db','name'),
                                   host   = self.config.get('db','host'),
                                   user   = self.config.get('db','user'),
                                   passwd = self.config.get('db','password'),
                                   cursorclass = MySQLdb.cursors.DictCursor )
            self._db.set_character_set(self._encoding)
            self._cursor = self._db.cursor()
            self._cursor.execute('SET NAMES '+self._encoding+';')
            self._cursor.execute('SET CHARACTER SET '+self._encoding+';')
            sql = 'SET character_set_connection='+self._encoding+';'
            self._cursor.execute(sql)
            
            self._log('Connected to DB :', self._db)
            if self._db == False:
                raise
        except Exception, ex:
            self._error('Unable connect to database', (ex, ex.args))    

    
    #--------------------------------------------------------------------------
    def checkDbConnection(self, db=None):
        '''
        Check connection and try to reconnect if it is broken
        '''
        try:
            if not db:
                db = self._db
            cursor = db.cursor()
            cursor.execute('SET NAMES '+self._encoding+';')
        except Exception, e:
            self._log('Re-connect to database', (e, e.args))
            self._connectToDb()
            
    #--------------------------------------------------------------------------
    def queryFetchAll(self, sql, args):
        '''
        Get fetched result of SQL query 
        '''  
        self._cursor.execute(sql, args)
        return self._cursor.fetchall()      



#===============================================================================
class FastMemcachedServer(FastServer):
    isMemcache   = True
    mc           = None
    cache_expire = 3600 # 1 hour
    
    #--------------------------------------------------------------------------
    def initMemcache(self):
        memcacheEnabled       = self.config.getint('memcache', 'enabled')
        
        if memcacheEnabled == 1:
            self.isMemcache = True
            import memcache
            memserver = self.config.get('memcache', 'server')
            self.cache_expire = self.config.getint('memcache', 'expire') * 60
            #if self.cache_expire == 0:
            #    self.cache_expire = 60*60 # default value 1 hour 

            self._log('Try connect to memcache [%s]' % memserver)
            self.mc = memcache.Client( [ memserver ], debug=1)
            self._log('Enabling Memcache [%s]' % self.mc)
        else:
            self.isMemcache = False
            
            
    #--------------------------------------------------------------------------
    def getCacheKey(self, function, args):
        '''
        Get cache key for server function calling
        '''
        return self.config_file+'---'+getCacheKey(function, args)


    #--------------------------------------------------------------------------
    def cachedResult(self, function, args):
        '''
        Get function result directly or from cache
        '''
        if self.isMemcache:
            key  = self.getCacheKey(function, args)

            self._log('Try memcache for key [%s]' % key)
            
            data = self.mc.get(key)

            if not data:
                self._log('Missed cache for [%s] - direct run' % key)
                data = function(args)
                self.mc.set(key, data, self.cache_expire)
            else:
                self._log('Memcache hit')
        else:
            data = function(args)
            
        return data
    
    #--------------------------------------------------------------------------
    def queryFetchAllCached(self, sql, args):
        '''
        Get cache SQL query
        '''
        if self.isMemcache:
            m = hashlib.md5()
            m.update(sql % args)
            
            key  = m.hexdigest()+'---'+toupleToString(args)

            self._log('Try memcache for sql [%s]' % key)
            data = self.mc.get(key)

            if not data:
                self._log('Missed cache for [%s] - direct run' % key)
                self.queryFetchAll(sql, args)
                self.mc.set(key, data, self.cache_expire)
            else:
                self._log('Memcache hit')
        else:
            data = self.queryFetchAll(sql, args)
            
        return data



