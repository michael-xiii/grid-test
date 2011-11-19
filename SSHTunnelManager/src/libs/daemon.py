#!/bin/sh
# /bin/env python
'''Daemon class'''
 
import sys, os, time, atexit
from signal import SIGTERM
 
class Daemon:
    actions = ['start', 'stop', 'restart']
    name    = ''
    port    = 0
            
    #----------------------------------------------------------------------
    """
    A generic daemon class.
       
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile=None, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        if not pidfile:
            self.pidfile = '/var/run/'+self.name.lower()+'-'+str(self.port)+'.pid'
        else:
            self.pidfile = pidfile
       
    #----------------------------------------------------------------------
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
                pid = os.fork()
                if pid > 0:
                        # exit first parent
                        sys.exit(0)
        except OSError, e:
                sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
                sys.exit(1)
        
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, ex:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (ex.errno, ex.strerror))
            sys.exit(1)
        
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)

        os.dup2(si.fileno(), sys.stdin.fileno())
        if sys.stdout.fileno() != -1:
            os.dup2(so.fileno(), sys.stdout.fileno())
        if sys.stderr.fileno() != -1:
            os.dup2(se.fileno(), sys.stderr.fileno())
        
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
  
    #----------------------------------------------------------------------------
    def delpid(self):
        os.remove(self.pidfile)

    #----------------------------------------------------------------------------
    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        pid = self.get_pid()
    
        if pid:
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
       
        # Start the daemon
        self.daemonize()
        self.run()

    
    #----------------------------------------------------------------------------
    def get_pid(self):
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        return pid
    
    #----------------------------------------------------------------------------
    def stop(self):
        """
        Stop the daemon
        """
        pid = self.get_pid()
        
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart
        
        self.kill_pid(pid)
        

    #----------------------------------------------------------------------------
    def kill_pid(self, pid):
        # Try killing the daemon process       
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
        
        

    #----------------------------------------------------------------------------
    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    #----------------------------------------------------------------------------
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        raise
           
           
    #----------------------------------------------------------------------------
    def processAction(self, argv):
        """
        Process action from command string
        """
        try:
            if len(argv) == 2:
                for action in self.actions:
                    if action == argv[1]:
                        print self.name+' is processing [%s]...' % action
                        eval('self.'+action+'()')
                        print '\t\t\t[Ok]'
                        return
                print 'Unknown action\n' + ( self.name + ' usage: %s '+"|".join(self.actions) ) % argv[0] # |reload
                sys.exit(2)
            else:
                print ( self.name + ' usage: %s '+"|".join(self.actions) ) % argv[0] # |reload
                sys.exit(2)
        except Exception, ex:
            print '\t\t\t[Error]', (ex)            