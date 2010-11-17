################################################################################
# $Date: 2010-03-26 15:30:06 -0400 (Fri, 26 Mar 2010) $
# $Rev: 970 $
# $Author: onelson $
################################################################################

import sys, os, re, maya
import pyPreflight.util
# These tests expect there to be an open maya scene available via the maya module

# From what I understand, python 3 will give us abstract classes and interfaces
# to work with.  For the time being, we are using the honor system.
class __Abstract():
    # if you override __init__ be careful to call _clearTrace
    def __init__(self):
        self._clearTrace()
    def _clearTrace(self):
        self._trace = []
        self._count = 0
    def _addMessage(self,message):
        self._trace.append('%s' % message)
    def isValid(self):
        self._clearTrace()
        return self._validate()
    # Override this method in subclasses - should return bool
    # if there are messages to attach to the trace during this method call
    # use self._addMessage(message)
    def _validate(self):
        raise NotImplementedError, 'this method needs to be implemented in the calling class'
    # Override this method in subclasses - should return string
    def getTestName(self):
        raise NotImplementedError, 'this method needs to be implemented in the calling class'
    # Override this method in subclasses - should return string
    def getDefaultMessage(self):
        raise NotImplementedError, 'this method needs to be implemented in the calling class'
    def getMessages(self):
        return  [self.getDefaultMessage()] + self.getTrace()
    def getTrace(self):
        return self._trace


# Just a skeleton test
class TemplateTest(__Abstract):
    def getTestName(self):
        pass
    def getDefaultMessage(self):
        pass
    def _validate(self):
        pass

class OutputFormatTest(__Abstract):
    def getTestName(self):
        return 'Checking that output filename format is of type "sequence"'
    def getDefaultMessage(self):
        return 'filename format is not a sequence type - could be single frame'
    def _validate(self):
        sequenceFlag = maya.cmds.getAttr('%s.%s' % (pyPreflight.util.getRenderSettingsNode(),'animation'))
        if 1 == sequenceFlag: return True
        return False

class FramePaddingTest(__Abstract):
    def getTestName(self):
        return 'Checking that "frame padding" is set to 4'
    def getDefaultMessage(self):
        return 'frame padding is not set to 4'
    def _validate(self):
        if 4 == maya.cmds.getAttr('%s.%s' % (pyPreflight.util.getRenderSettingsNode(),'extensionPadding')): return True
        return False


class PSDFileTest(__Abstract):
    def getTestName(self):
        return 'Checking for PSD Files'
    def getDefaultMessage(self):
        return 'found [%d] PSD Files' % self._count
    def _validate(self):
        self._count = 0
        files = maya.cmds.ls(type='file') or []
        pattern = re.compile('\.psd$', re.IGNORECASE)
        
        
        badFiles = [f for f in files if pattern.search(maya.cmds.getAttr('%s.%s' % (f, 'fileTextureName')))]
        if not badFiles: return True
        self._count = len(badFiles)
        for file in badFiles:
            self._addMessage(file)
        return False
    
class PSDNodeTest(__Abstract):
    def getTestName(self):
        return 'Checking for psdFileTex nodes'
    def getDefaultMessage(self):
        return 'found [%d] psdFileTex nodes' % self._count
    def _validate(self):
        self._count = 0
        nodes = maya.cmds.ls(type='psdFileTex') or []
        if not nodes: return True
        self._count = len(nodes)
        for node in nodes:
            self._addMessage(node)
        return False

# This is one of the few tests we have that needs to accept args for configuration
# further down the line (as need arises) we'll add startup and shutdown methods to
# the run routine (currently isValid) to deal with this problem 
class NameLengthTest(__Abstract):
    # 246 is how many characters you have  left to play with for a 
    # file name after .####.ex
    def __init__(self, threshold=246):
        self._clearTrace()
        self._threshold = threshold
    def getTestName(self):
        return 'Checking for node names longer than [%d] characters' % self._threshold
    def getDefaultMessage(self):
        return 'found [%d] long names' % self._count
    def _validate(self):
        self._count = 0
        geo = maya.cmds.ls(geometry=True) or []
        longNames = [g for g in geo if len(g) > self._threshold]
        if not longNames: return True
        self._count = len(longNames)
        self._addMessage('Long node names can result in your render job failing during ribgen')
        self._addMessage('Adjust your node names, or node hierarchy to shorten them.')
        for name in longNames:
            self._addMessage(name)
        return False

class RenderableCamTest(__Abstract):
    def getTestName(self):
        return 'Checking cameras with "renderable" attribute set'
    def getDefaultMessage(self):
        return 'found [%d] cameras set as "renderable"' % self._count
    def _validate(self):
        self._count = 0
        cameras = maya.cmds.ls(cameras=True) or []
        renderCams = [cam for cam in cameras if maya.cmds.getAttr('%s.renderable' % cam)]
        self._count = len(renderCams)
        if 1 == self._count:
            return True
        if 0 == self._count:
            self._addMessage("you need at least one renderable camera or you won't get any frames back")
        else:
            self._addMessage("having more than one renderable camera can kill your render times")
        return False

class CamLightsTest(__Abstract):
    def getTestName(self):
        return 'Checking for lights attached to cameras'
    def getDefaultMessage(self):
        return 'found [%d] cameras with lights attached' % self._count 
    def _validate(self):
        self._count = 0 # init the node count
        lights = maya.cmds.ls(lights=True) or []
        badLights = [light for light in lights if maya.cmds.listConnections(light,type="camera")]
        self._count = len(badLights)
        if not self._count:
            return True
        else:
            for node in badLights:
                self._addMessage(node)
        return False

# gathers a list of all geometry "shape" nodes then filters the list down to 
# only contain ones that are connected to more than one shader
# then is passed to _traceShapesToTransforms to get actual 
# viewport-clickable node names
class MultipleShaderTest(__Abstract):
    def getTestName(self):
        return 'Checking for multipleshaders on individual shape nodes'
    def getDefaultMessage(self):
        return 'shape nodes [%d] with multiple shaders attached found' % self._count
    def _validate(self):
        self._count = 0
        geo = maya.cmds.ls(geometry=True)
        if not geo:
            return True
        badShapes = []
        for shape in geo:
            shaders = maya.cmds.listConnections(shape,destination=True,source=False,plugs=False,type="shadingEngine")
            # the following reduction came from greg's script
            # removes 'false positives' generated by instances 
            # that will actually be fine
            maya.cmds.select(shaders, noExpand=True)
            shaders = maya.cmds.ls(selection=True)
            maya.cmds.select(clear=True)
            if shaders and len(shaders) > 1:
                badShapes.append(shape)
        if not badShapes:
            return True
        self._addMessage('transform nodes connected to shapes:')
        import pyPreflight.util
        transNodes = [trans for trans in pyPreflight.util.traceShapesToTransforms(badShapes)]
        self._count = len(transNodes)
        for node in transNodes: self._addMessage(node)
        return False