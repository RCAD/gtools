################################################################################
# $Date: 2009-06-22 16:12:37 -0400 (Mon, 22 Jun 2009) $
# $Rev: 945 $
# $Author: onelson $
################################################################################

import pyPreflight.writer
class __Abstract():
    def __init__(self):
        self._writer = None
        self._tests = [] # list of tests to run
        self._cleanup() # initializes the result lists
    def setWriter(self, writer):
        self._writer = writer
        return self
    def _getWriter(self):
        if None == self._writer:
            self._writer = pyPreflight.writer.Default()
        return self._writer
    def _record(self, test):
        self._getWriter().write(test)
    def setTests(self, Ltests):
        self._tests = Ltests or []
    def addTests(self, Ltests):
        for test in Ltests:
            self.addTest(test)
    def addTest(self, test):
        self._tests.append(test)
        return self
    def _getTests(self):
        return self._tests
    def run(self):
        self._run()
        self._cleanup()
    def _run(self):
        raise NotImplementedError, 'this method needs to be implemented in the calling class'
    def _cleanup(self):
        self._failures = []
        self._passes = []
    
class Default(__Abstract):
    def _record(self, test):
        import sys
        scribe = sys.stdout.write
        if test.isValid():
            self._passes.append(test)
            scribe('.')
        else:
            self._failures.append(test)
            scribe('F')
            
    def _run(self):
        for test in self._getTests():
            self._record(test)

        print
        print '[%d] failures' % len(self._failures)
        print '[%d] passes' % len(self._passes)
        print 
        # once results are collected, report the failures
        if self._failures:
            print 'Failure Details:\n',('-'*80)
            for test in self._failures:
                print self._getWriter().write(test)
            print '-'*80
        
            