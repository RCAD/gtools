#============================================================
# Python port of scripts by Bohdon Sayre (see below comments)
# @author onelson@ringling.edu bsayre@c.ringling.edu
#============================================================

#============================================================
#    Ringling Rendering Menu
#    0.1
#    
#    created by Bohdon Sayre
#    bsayre@c.ringling.edu
#    
#    unique prefix: rrMenu
#    
#    Description:
#        This script creates a menu for access to
#        several rendering scripts including the
#        job submission GUI
#
#    Version 0.1:
#                >  Includes GUI only
#============================================================                
#    Ringling Rendering Submission UI
#    0.8
#    
#    created by Bohdon Sayre
#    bsayre@c.ringling.edu
#    
#    unique prefix: rrUI
#    
#    Description:
#        This script provides a gui for submitting jobs
#        to the ringling rendering grid.
#
#    Version 0.1:
#                > Auto grabbing of current scene information
#    
#    TODO:
#        finish submission checks
#        format submission string properly
#        send information to web cgi
#============================================================

import maya.OpenMayaMPx
import maya.cmds
import maya.mel
import math
import sys
import os


class RinglingSubmit:
    
    def __init__(self, menuName='rrMenu', windowName='rrUIWin'):
        self.NO_COMMAND = ''
        self._menuName = menuName
        self._windowName = windowName
        self._windowTitle = 'Ringling Render Submission 0.1'
        # this hack allows us to get at the main maya window name
        self._mainWindowName = maya.mel.eval('$tmpVar=$gMainWindow')
        
        #============================================================
        # Blarg!
        # Due to a limitation in (life?) the way the whole 
        # maya/mel/python/gui relationship is setup, we need to 
        # provide some global scope methods to get fileBrowserDialog
        # interactions to work correctly
        #============================================================
        maya.mel.eval("""
        global proc rrUISceneDirHandler(string $result, string $type) {
            //changes:
            //  scene dir field
            //  proj dir field
            string $sceneDir = `rrMAYAPath $result`;
            //beacuse sceneDir was MAYAPathed, proj doesn't have to be
            string $projDir = `rrProjPath $sceneDir`;
            
            textField -e -tx $sceneDir rrUISceneDirField;
            //only auto-get project if it was different than scene dir
            if ($projDir != $sceneDir)
                textField -e -tx $projDir rrUIProjDirField;
        }
        
        
        global proc rrUIProjDirHandler(string $result, string $type) {
            //changes:
            //  proj dir field
            string $projDir = `rrMAYAPath $result`;
            textField -e -tx $projDir rrUIProjDirField;
        }
        """)
        
    def unloadMenu(self):
        if maya.cmds.menu(self._menuName, exists=True):
            maya.cmds.deleteUI(self._menuName)
    def loadMenu(self, parentName=None):
        self.unloadMenu()
        if parentName and maya.cmds.menu(parentName, exists=True):
            maya.cmds.menuItem(self._menuName, label='Ringling Rendering', subMenu=True, parent=parentName)
        else:
            maya.cmds.menu(self._menuName, tearOff=True, label='Ringling Rendering', allowOptionBoxes=True, parent=self._mainWindowName)
        maya.cmds.menuItem('rrMenuSubmitItem', label='Submit a job', command=self.loadSubmitGUI, parent=self._menuName)
        maya.cmds.menuItem('rrMenuRenderMeItem', label='Render me!', command=self.NO_COMMAND, parent=self._menuName)

    def getScenePicker(self, args=None):
        # fileBrowserDialog -fileCommand "rrUISceneHandler" -mode 0 -windowTitle "Choose a scene file..." -dialogStyle 1 -fileType "Maya ASCII (*.ma)" -actionName "Open" -operationMode "" -includeName "" -filterList "Maya ASCII (*.ma),*.ma"
        (path,type) = maya.cmds.fileBrowserDialog( m=0, dialogStyle=1, fileCommand=rrUISceneHandler, fileType='mayaAscii, mayaBinary', filterList='Maya Scene (*.ma, *.mb),*.ma;*.mb', actionName='Select', windowTitle='Choose a scene file...')
    
    def getSceneDirPicker(self, args=None):
        # fileBrowserDialog -fileCommand "" -mode 4 -windowTitle "Choose the scene file's directory..." -dialogStyle 1 -fileType "Directory" -actionName "Choose" -operationMode "" -includeName "" -filterList "Directory"
        maya.cmds.fileBrowserDialog(mode=4, dialogStyle=1, fileCommand=rrUISceneDirHandler, fileType='directory', actionName='Select', windowTitle='Choose the scene file\'s directory...')
        

    # ported from rrSubmit
    def unloadSubmitGUI(self, args=None):
        if maya.cmds.window(self._windowName, exists=True):
            maya.cmds.deleteUI(self._windowName)
    def loadSubmitGUI(self, args=None):
        # check for pre-existing window
        if maya.cmds.window(self._windowName, exists=True):
            maya.cmds.deleteUI(self._windowName)
        # build the window
        maya.cmds.window(self._windowName,
                         width=100,
                         height=100,
                         menuBar=True,
                         sizeable=True,
                         maximizeButton=True,
                         resizeToFitChildren=True,
                         title=self._windowTitle,
                         minimizeCommand="maya.cmds.window('%s', edit=True, title='%s')" % (self._windowName,self._windowTitle),
                         )
        maya.cmds.menu('Edit')
        maya.cmds.menuItem('Refresh', command=self.getCurSceneInfo)
        
        # Todo: implement this feature
        maya.cmds.menu('Options')
        maya.cmds.menuItem(label='Auto turn on statistics', enable=False, command=self.NO_COMMAND)
        
        # build window contents
        formLayoutName = maya.cmds.formLayout(numberOfDivisions=100)
        
        # ui type switch allows for scene info from current scene OR other scenes to be loaded
        typeLayout = maya.cmds.columnLayout(adj=True)
        maya.cmds.radioButtonGrp(label="Scenes to submit", 
                                 nrb=2, 
                                 columnWidth3=[120,60,60],
                                 labelArray2=['Current','Other'],
                                 data1=1,
                                 data2=0,
                                 # couldn't figure out how to make it call uiTypeSwitch(data)  
                                 # so I'm using 2 separate callback methods
                                 onCommand1=self.setUiModeCurrentScene, 
                                 onCommand2=self.setUiModeOtherScene,
                                 select=1
                                 )
        maya.cmds.separator(height=10)
        
        # reach back up to the main window layout
        maya.cmds.setParent(formLayoutName)
        
        # scene file information, disabled by default because current scene is default
        fileInfoLayout = maya.cmds.frameLayout(borderStyle='etchedIn', label='Maya File Information', labelIndent=8, labelAlign='center', marginHeight=5)
        browserLayout = maya.cmds.columnLayout()
        maya.cmds.rowLayout(numberOfColumns=3, columnWidth3=[85,300,50], columnAlign3=['right','left','center'])
        maya.cmds.text(label='Scene File', width=80)
        maya.cmds.textField(width=300)
        maya.cmds.symbolButton(image='navbuttonbrowse.xpm', command=self.getScenePicker)
        
        maya.cmds.setParent(browserLayout)
        maya.cmds.rowLayout(numberOfColumns=3, columnWidth3=[85,300,50], columnAlign3=['right','left','center'])
        maya.cmds.text(label='Scene Directory', width=80)
        maya.cmds.textField(width=300)
        maya.cmds.symbolButton(image='navbuttonbrowse.xpm', command=self.getSceneDirPicker)
        
        # render the gui
        maya.cmds.showWindow(self._windowName)
    # end gui method!
    
    def setUiModeCurrentScene(self, arg):
        self._uiTypeSwitch(mode=1)
    def setUiModeOtherScene(self, arg):
        self._uiTypeSwitch(mode=0)
    # ported from rrUISubmit
    def submit(self):
        pass
    # ported from rrUITypeSwitch
    def _uiTypeSwitch(self, mode=1):
        print mode
        pass
    # ported from rrUIGetCurSceneInfo
    def getCurSceneInfo(self, args=None):
        pass
    # ported from rrProjPath
    def _projPath(self, path):
        Lparts = path.split('/')
        if not Lparts:
            return None
        try:
            index = Lparts.index('scenes')
        except ValueError:
            sys.stderr.write("scenes dir not found in path %s\n" % path)
            sys.stderr.write("unable to locate project dir\n")
            return None
        return '/'.join(Lparts[:index])+'/'
    # ported from rrMAYAPath
    def mayaPath(self, path):
        pass



# ported from rrUISceneHandler
def rrUISceneHandler(*args):
    return args
    # extract last dir name
    #
    
#    string $scene = `match "[^/\\]*$" $result`;
#    string $sceneDir = `substitute ("/"+$scene) $result ""`;
#    $sceneDir = `rrMAYAPath $sceneDir`;
#    //beacuse sceneDir was MAYAPathed, proj doesn't have to be
#    string $projDir = `rrProjPath $sceneDir`;
#    //remove .ma
#    $scene = `substitute ".ma$" $scene ""`;
#    
#    textField -e -tx $scene rrUISceneField;
#    textField -e -tx $sceneDir rrUISceneDirField;
#    //only auto-get project if it was different than scene dir
#    if ($projDir != $sceneDir)
#        textField -e -tx $projDir rrUIProjDirField;

# ported from rrUISceneDirHandler
def rrUISceneDirHandler(*args):
    return args


rs = RinglingSubmit()
# initialize the script plug-in
def initializePlugin(mobject):
    # this hack allows us to get at the main maya window name
    gMainWindow = maya.mel.eval('$tmpVar=$gMainWindow')
    # the parentName is used as an attempted menu to 
    # nest in if not present, a new menu is added
    rs.loadMenu(parentName='%s|dilloTools' % gMainWindow)

def uninitializePlugin(mobject):
    rs.unloadMenu()
    rs.unloadSubmitGUI()
    sys.stdout.write("unloading plugin\n")
