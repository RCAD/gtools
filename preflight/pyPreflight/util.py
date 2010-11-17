################################################################################
# $Date: 2009-07-21 11:24:33 -0400 (Tue, 21 Jul 2009) $
# $Rev: 946 $
# $Author: onelson $
################################################################################

import maya

# takes a list of "shape" nodes and returns transform nodes (aka actual surfaces)
def traceShapesToTransforms(shapeList):
    # note, the allParents param gives us ALL the 
    # main transform nodes related to the shape - important for 
    # instanced geometry where 1 shape is attached to 2 transforms (the 
    # actual surfaces) and can have different shaders - thus killing renderman
    if shapeList:
        return maya.cmds.listRelatives(shapeList, allParents=True, fullPath=True)

# renderman specific checks
def sceneHasRenderMan():
    if maya.cmds.ls('renderManGlobals'): return True
    return False

def getRenderSettingsNode(): 
    L = maya.cmds.ls(type='renderGlobals')
    # not sure this is proper - ls returns a list, we return the first index from that list
    return L[0]
def getLongestNodeName():
    nodes = maya.cmds.ls(geometry=True)
    if not nodes: return None
    return max(nodes, key=len) 