# coding: utf-8
# This function is based a JMG script, shared in FreeCAD users forum (2015)

import os
import FreeCAD as App
import Part
import math
from freecad.metalwb import ICONPATH
from freecad.metalwb import RESOURCESPATH

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
    from DraftTools import translate
    from PySide.QtCore import QT_TRANSLATE_NOOP
else:
    # \cond
    def translate(ctxt, txt):
        """
        Return a translated string.
        ctxt : context in which the 'text' is in ; txt  : actual text that will be translated.
        """
        return txt


    def QT_TRANSLATE_NOOP(ctxt, txt):
        """
        Return an untranslated string, to translate later.
        Mostly needed for C++ where not all strings can handle translation.
        """
        return txt
    # \endcond

class _CommandOverlap:
    def __init__(self):
        pass

    def GetResources(self):
        "Tool resources"
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "overlap.svg"),
            "MenuText": QT_TRANSLATE_NOOP("MetalWB", "Overlap detection"),
            "Accel": "C, B",
            "ToolTip": QT_TRANSLATE_NOOP("MetalWB", "<html><head/><body><p><b>Detect overlap</b> \
                    <br><br> \
                    For selected objects. \
                    </p></body></html>"),
        }

    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        """Define what happen when the user clic on the tool"""
        object_list = []
        for obj in App.Gui.Selection.getSelectionEx():
            obj = obj.Object
            object_list.append(obj)

        for n in range(len(object_list)):
            object_A = object_list[n]
            for i in range(len(object_list)):
                if i <= n:
                    pass

                else:
                    object_B = object_list[i]
                    common = object_A.Shape.common(object_B.Shape)
                    if common.Volume > 0.0:
                        App.Console.PrintMessage(
                            '-Intersection- ' + object_A.Name + ' with ' + object_B.Name + '\n')
                        App.Console.PrintMessage('Common volume' + str(common.Volume) + '\n' + '\n')

                        intersection_object = App.ActiveDocument.addObject('Part::Feature')
                        intersection_object.Shape = common
                        intersection_object.ViewObject.ShapeColor = (1.0, 0.0, 0.0, 1.0)
                        object_A.ViewObject.Transparency = 80
                        object_B.ViewObject.Transparency = 80


if App.GuiUp:
    Gui.addCommand("OverlapDetect", _CommandOverlap())