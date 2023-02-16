# coding: utf-8

import os
import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui

    from PySide import QtCore, QtGui
    from DraftTools import translate
    from PySide.QtCore import QT_TRANSLATE_NOOP
else:
    # \cond
    def translate(ctxt, txt):
        return txt
    def QT_TRANSLATE_NOOP(ctxt, txt):
        return txt
    # \endcond



class _CommandTrim:
    """This tool create a Draft Line based on the target of the prfile then activated Draft Trimex on it
    The difference between the target and the Draft Line allow us to add offset to profile object"""
    def __init__(self):
        pass

    def GetResources(self):
        "Tool resources"
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "trim_extend.svg"),
            "MenuText": QT_TRANSLATE_NOOP("MetalWB", "MetalWB_Trim"),
            "Accel": "T, R",
            "ToolTip": "<html><head/><body><p><b>Ajuster le profilé.</b> \
                    <br><br> \
                    Ajuste le profilé en longueur. \
                    </p></body></html>",
        }

    def IsActive(self):
        if App.ActiveDocument:
            self.doc = App.ActiveDocument
            if len(Gui.Selection.getSelection()) == 1:
                if hasattr(Gui.Selection.getSelection()[0], 'Target'):
                    return True
                elif hasattr(Gui.Selection.getSelection()[0], 'CornerType'):
                    return True
        return False

    def Activated(self):
        """Define what happen when the user clic on the tool"""
        import Draft
        self.part = self.getMetalWBProfile(Gui.Selection.getSelection()[0])
        self.original_length = self.part.Height.Value
        start_point = App.Vector()
        end_point = App.Vector(0, 0, self.original_length)
        self.doc.openTransaction("MetalWB Trim/extend")
        self.draft_line = Draft.makeLine(start_point, end_point)
        self.draft_line.Placement = self.part.Placement
        self.draft_line.ViewObject.LineWidth = 10.00
        self.draft_line.ViewObject.PointSize = 15.00
        self.draft_line.recompute()
        self.start = self.draft_line.Start
        self.end = self.draft_line.End
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(self.draft_line)

        Gui.runCommand('Draft_Trimex',0)

        # Timer to check when ActiveDialog is over meaning that the Draft Trimex command is done
        self.tool_timer = QtCore.QTimer()
        self.tool_timer.setInterval(120)
        self.tool_timer.timeout.connect(self.check)
        self.tool_timer.start()

    def check(self):
        if not Gui.Control.activeDialog():
            self.tool_timer.stop()
            self.finish_trim_command()

    def finish_trim_command(self):
        offset = self.draft_line.Length.Value - self.original_length
        precision = 0.001
        if ( self.start - self.draft_line.Start ).Length <= precision :
            self.part.OffsetB += offset
        elif ( self.start - self.draft_line.End ).Length <= precision :
            self.part.OffsetB += offset
        elif ( self.end - self.draft_line.Start ).Length <= precision :
            self.part.OffsetA += offset
        elif ( self.end - self.draft_line.End ).Length <= precision :
            self.part.OffsetA += offset
        else:
            App.Console.PrintWarning("Please, contact workbench developper about this case")

        App.ActiveDocument.removeObject(self.draft_line.Name)
        self.doc.commitTransaction()
        App.activeDocument().recompute(None,True,True)

    
        
    def getMetalWBProfile(self, link):
        while True:
            if hasattr(link, "Target" ):
                return link
            elif hasattr(link, "CornerType"):
                link = link.TrimmedBody


if App.GuiUp:
    Gui.addCommand("MetalWB_Trim", _CommandTrim())