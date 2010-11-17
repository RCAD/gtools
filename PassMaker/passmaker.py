"""
# example:
win = PassMakerWindow()
win.show()
"""

import maya.cmds as cmds
import maya.mel as mel

class PassMakerError(Exception): pass

def melPrint(msg):
    """
    Prints using mel.eval.
    """
    msg = msg.replace('\\', '\\\\')
    msg = msg.replace('"', '\\"')
    mel.eval(r' print ("%s\n")' % msg)

def rmanLoaded():
    """
    Ensures that the RenderMan for Maya plug-in is loaded.
    """
    if not cmds.pluginInfo('RenderMan_for_Maya', q=True, loaded=True):
        melPrint('// loading RenderMan for Maya plug-in...')
        try:
            cmds.loadPlugin('RenderMan_for_Maya')
            return True
        except RuntimeError, err:
            return False
    else:
        return True


class Pass(object):
    if not rmanLoaded():
        raise PassMakerError('The RenderMan plug-in could not be found')

    @staticmethod
    def valid_channels(): return mel.eval('rmanGetChannelClasses;')

    """
    'name' will provide access to the pass node name
    """
    #Using the Final Defaults, instead of creating new Passes...
    _pass_node = mel.eval('rmanGetDefaultPass "Final";')
    name = _pass_node # we'll treat this with a decorator
    channels = []

    def __str__(self): return repr(self.name)

    def _create_pass(self): 
        """
        Selectively creates new pass nodes
        """
        if not self._pass_node:
            self._pass_node = mel.eval('rmanCreatePass Final;')
        return self._pass_node

    """
    returns current pass node name, creating new a node as needed
    """
    #using the Final Defaults...
    #name = property(_create_pass)

    def validate(self):
        """
        Ensures that Renderman is loaded, and channels are expected values.
        """
        valid = self.valid_channels()
        filtered_list = []
        
        if not self.channels: raise PassMakerError, 'must select at least one channel'
        
        for chan in self.channels:  
            if chan not in valid: raise PassMakerError,'invalid channel: [%s]' % chan
            # remove potential duplicates
            if chan not in filtered_list: filtered_list.append(chan)
        self.channels = filtered_list
    
    def make(self):
        self.validate()
        # reset the reference to the pass node before creation
        self._pass_node = None
        
        cmd = 'rmanAddOutput %s "%s";' % (self.name,','.join(self.channels))
        mel.eval(cmd)
        return cmd

class PassMakerWindow(object):
    
    _name = 'RinglingPassMakerWindow'
    _title = 'Pass Maker'
    _makeBtnLabel = 'Make Pass'
    _pass = Pass()
    
    NULL = ''
    
    def show(self):
        # check for pre-existing window
        if cmds.window(self._name, exists=True):
            cmds.deleteUI(self._name)
        # build the window
        cmds.window(self._name,
                         menuBar=False,
                         sizeable=True,
                         maximizeButton=False,
                         resizeToFitChildren=True,
                         title=self._title,
                         minimizeCommand="cmds.window('%s', edit=True, title='%s')" % (self._name,self._title),
                         )
                
        # build window contents
        mainForm = cmds.formLayout(nd=100)
        if True: #contents of mainForm
            self.textList = cmds.textScrollList(selectCommand=self.textList_sel, allowMultiSelection=True, append=Pass.valid_channels())
            self.textListInfo = cmds.text(l='Select channels, then click %s' % self._makeBtnLabel)
            self.outCmdText = cmds.text(l='Command (middle mouse drag to shelf):', en=False)
            self.outCmdField = cmds.scrollField(wordWrap=True, editable=False, height=80)
            self.makePassBtn = cmds.button(label=self._makeBtnLabel, command=self.makePass_cmd, height=30)
        
        cmds.formLayout(mainForm, e=True, ap=[(self.textList, 'left', 0, 0), (self.textList, 'right', 0, 100), (self.textList, 'top', 0, 0)], ac=[(self.textList, 'bottom', 2, self.textListInfo)])
        cmds.formLayout(mainForm, e=True, ap=[(self.textListInfo, 'left', 4, 0), (self.textListInfo, 'right', 4, 100)], ac=[(self.textListInfo, 'bottom', 2, self.outCmdText)])
        cmds.formLayout(mainForm, e=True, ap=[(self.outCmdText, 'left', 4, 0)], ac=[(self.outCmdText, 'bottom', 2, self.outCmdField)])
        cmds.formLayout(mainForm, e=True, ap=[(self.outCmdField, 'left', 0, 0), (self.outCmdField, 'right', 0, 100)], ac=[(self.outCmdField, 'bottom', 2, self.makePassBtn)])
        cmds.formLayout(mainForm, e=True, ap=[(self.makePassBtn, 'left', 0, 0), (self.makePassBtn, 'right', 0, 100), (self.makePassBtn, 'bottom', 0, 100)])
        
        # edit window size now that controls have been initialized, then render the gui
        cmds.window(self._name, e=True, width=220, height=680)
        cmds.showWindow(self._name)
    
    def textList_sel(self, *args):
        self._pass.channels = cmds.textScrollList(self.textList, query=True, selectItem=True)
        if self._pass.channels:
            cmds.text(self.textListInfo, edit=True, label='%d channel(s)' % len(self._pass.channels) )
        else:
            cmds.text(self.textListInfo, edit=True, label='Select channels, then click %s' % self._makeBtnLabel)
        
    def makePass_cmd(self, *args):
        try:
            cmd = self._pass.make()
            cmds.scrollField(self.outCmdField, edit=True, text=cmd)
            melPrint('// %s' % cmd)
        except PassMakerError, err:
            mel.eval('warning "%s";' % err)