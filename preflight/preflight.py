################################################################################
# $Date: 2009-07-21 15:44:34 -0400 (Tue, 21 Jul 2009) $
# $Rev: 947 $
# $Author: onelson $
################################################################################
#
# This script can be run one of two ways (see the very last code block).
# It can be run from the command line (using the mayapy executable, followed by
# the script name and path to a scene file as an arg), or it can be run from 
# within maya (as a plugin). 
# The Plugin will automatically register a MEL command 'preflight'.
#
# Usage:
#    From the command line: mayapy preflight.py /path/to/scene/file.mb
#    From within maya: 'preflight' in the MEL command line, or script editor
################################################################################

import sys, os, maya

# calls each of the 'test' methods and interpretes the return values 
def report():
    import pyPreflight.testcase as testcase 
    import pyPreflight.runner as runner
    import pyPreflight.writer as writer 
    import pyPreflight.util
    Ltests = [
              testcase.OutputFormatTest(),
              testcase.FramePaddingTest(),
              testcase.PSDFileTest(),
              testcase.PSDNodeTest(),
            # 246 is actually the default
            # I just passed the argument for clarity
              testcase.NameLengthTest(246), 
              testcase.RenderableCamTest(),
              testcase.CamLightsTest(),
              testcase.MultipleShaderTest()
              ]
    suite = runner.Default()
#    suite.setWriter(writer.HTML())
    suite.setTests(Ltests)
    if not pyPreflight.util.sceneHasRenderMan():
        print 'Skipping renderman settings checks - renderman globals node not found'
    suite.run()
    
    
    
def main():
    import optparse
    usage = "usage: %prog [options] /path/to/scene/file"
    parser = optparse.OptionParser(usage=usage)
    (options,args) = parser.parse_args()
    if not args:
        sys.exit(parser.print_help())
    sceneFile = os.path.realpath(os.path.expanduser(args[0]))
    if not sceneFile:
        parser.error("could not find scene file: %s" % sceneFile)
    if not os.path.exists(sceneFile) and not os.path.isfile(sceneFile):
        print "Can't find maya scene [%s]\nDoes it exist for real?" % sceneFile
        sys.exit(parser.print_help())
    import maya.standalone
    import maya.OpenMaya
    maya.standalone.initialize(name='preflight')
    fh = maya.OpenMaya.MFileIO()
    fh.open(sceneFile)
    sys.exit(report())

if __name__ == '__main__': # run in command line mode
    sys.exit(main())
else: # run as a plugin
    import maya.OpenMayaMPx as OpenMayaMPx
    kPluginCmdName="preflight"
    
    class scriptedCommand(OpenMayaMPx.MPxCommand):
        def __init__(self):
            OpenMayaMPx.MPxCommand.__init__(self)
        def doIt(self,args):
            return report()
            
    def cmdCreator():
        # Create the command
        return OpenMayaMPx.asMPxPtr( scriptedCommand() )

# I believe this method only needs to exist if the scripted command takes args
# since I think it's used to generate the response of MEL's "help commandName"
# Syntax creator
#    def syntaxCreator():
#        syntax = OpenMaya.MSyntax()
#        return syntax

    # Initialize the script plug-in
    def initializePlugin(mobject):
        mplugin = OpenMayaMPx.MFnPlugin(mobject, "Autodesk", "1.0", "Any")
        try:
            mplugin.registerCommand( kPluginCmdName, cmdCreator )
        except:
            sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
            raise
    
    # Uninitialize the script plug-in
    def uninitializePlugin(mobject):
        mplugin = OpenMayaMPx.MFnPlugin(mobject)
        try:
            mplugin.deregisterCommand( kPluginCmdName )
        except:
            sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )
            raise