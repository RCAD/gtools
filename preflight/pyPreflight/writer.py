################################################################################
# $Date: 2010-03-26 15:30:06 -0400 (Fri, 26 Mar 2010) $
# $Rev: 970 $
# $Author: onelson $
################################################################################


class __Abstract():
    def __init__(self):
        self._decoration = '%s\n'
    def _decorate(self, message):
        return self._decoration % message
    def write(self, test):
        raise NotImplementedError, 'this method needs to be implemented in the calling class'
    
class Default(__Abstract):
    def write(self, test):
        if not test.isValid():
            output = self._decorate(test.getTestName())
            output += self._decorate(test.getDefaultMessage())
            trace = test.getTrace()
            if trace:
                trace_str = '\n'.join(trace)
                if 1024 < len(trace_str):
                    trace_str = trace_str[:1024]
                    trace = trace_str.splitlines()
                    trace.append('... message truncated ...')
                output += self._decorate('\n'.join(trace))
            return output
            
class HTML(__Abstract):
    def write(self, test):
        if not test.isValid():
            template = "<dl>\n\t<dt>\n%s\t</dt>\n\t<dd>\n%s\t</dd>\n<dl>"
            title = self._decorate(test.getTestName()+': '+test.getDefaultMessage())
            trace = self._decorate('<pre class="trace">%s</pre>' % '\n'.join(test.getTrace()))
            return template % (title,trace)
            