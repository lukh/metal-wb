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

class _CommandmyCube:
    def __init__(self):
        pass

    def GetResources(self):
        "Tool resources"
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "box.svg"),
            "MenuText": QT_TRANSLATE_NOOP("StarterKit", "MyCube"),
            "Accel": "C, B",
            "ToolTip": "<html><head/><body><p><b>Ajouter un cube.</b> \
                    <br><br> \
                    Aux dimensions de 15 mm. \
                    </p></body></html>",
        }

    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        """Define what happen when the user clic on the tool"""
        self.create_cube(1000.0)


    def create_cube(self, dimensions):
        """
        Create a cube
        :param dimensions: float
        """
        my_cube = App.ActiveDocument.addObject("Part::Box", "Box")
        my_cube.Label = "Cube"
        my_cube.Length = dimensions
        my_cube.Width = dimensions
        my_cube.Height = dimensions/2
        view_obj = Gui.ActiveDocument.getObject(my_cube.Name)
        view_obj.DisplayMode = "Wireframe"
        my_cube.ViewObject.ShapeColor = (1.00, 1.00, 1.00)
        my_cube.ViewObject.Transparency = 100
        my_cube.ViewObject.LineColor = (0.33, 0.67, 1.00)


if App.GuiUp:
    Gui.addCommand("MyCube", _CommandmyCube())