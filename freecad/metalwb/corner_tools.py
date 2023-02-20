# coding: utf-8

import FreeCAD as App
#translate = App.Qt.translate
import Part, ArchCommands
import BOPTools.SplitAPI
import os
import math
from freecad.metalwb import ICONPATH
from freecad.metalwb import RESOURCESPATH
from BimTranslateUtils import *

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
    #from DraftTools import translate
    #from PySide.QtCore import QT_TRANSLATE_NOOP

# dummy function for the QT translator
def QT_TRANSLATE_NOOP(ctxt,txt): 
    return txt

# use latest available translate function
if hasattr(App, "Qt"):
    translate = App.Qt.translate
else:
    from DraftTools import translate


def makeCorner(trimmedBody=None, trimmingBoundary=None):
    doc = App.ActiveDocument
    corner = doc.addObject("Part::FeaturePython","Corner")
    Corner(corner)
    ViewProviderCorner(corner.ViewObject)
    corner.TrimmedBody = trimmedBody
    corner.TrimmingBoundary = trimmingBoundary
    doc.recompute()
    return corner


class Corner:
    def __init__(self, obj):
        ''' Add some custom properties to our box feature '''
        obj.addProperty("App::PropertyLink","TrimmedBody","Corner", QT_TRANSLATE_NOOP("App::Property", "Body to be trimmed")).TrimmedBody=None
        obj.addProperty("App::PropertyLinkSubList","TrimmingBoundary","Corner", QT_TRANSLATE_NOOP("App::Property", "Bodies that define boundaries")).TrimmingBoundary=None
        #corner_types = ["End Trim", "End Miter", "End Butt1", "End Butt2",]
        corner_types = ["End Trim", "End Miter",]
        obj.addProperty("App::PropertyEnumeration","CornerType","Corner", QT_TRANSLATE_NOOP("App::Property", "Corner Type")).CornerType=corner_types
        cut_types = ["Coped cut", "Simple cut",]
        obj.addProperty("App::PropertyEnumeration","CutType","Corner", QT_TRANSLATE_NOOP("App::Property", "Cut Type")).CutType=cut_types
        obj.Proxy = self

    def onChanged(self, fp, prop):
        ''' Print the name of the property that has changed '''
        #App.Console.PrintMessage("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        ''' Print a short message when doing a recomputation, this method is mandatory '''
        App.Console.PrintMessage("Recompute {}\n".format(fp.Name))
        #TODO: Put these methods in proper functions
        if fp.TrimmedBody is None:
            return
        if len(fp.TrimmingBoundary) == 0:
            return
        
        cut_shapes = []
        
        if fp.CornerType == "End Trim":
            if fp.CutType == "Coped cut":
                shapes = [x[0].Shape for x in fp.TrimmingBoundary]
                shps = BOPTools.SplitAPI.slice(fp.TrimmedBody.Shape, shapes, mode="Split")
                for solid in shps.Solids:
                    x = fp.TrimmedBody.Shape.CenterOfGravity.x
                    y = fp.TrimmedBody.Shape.CenterOfGravity.y
                    z = fp.TrimmedBody.Shape.CenterOfGravity.z
                    if not solid.BoundBox.isInside(x, y, z):
                        cut_shapes.append(Part.Shape(solid))
                
            elif fp.CutType == "Simple cut":
                cut_shape = Part.Shape()
                for link in fp.TrimmingBoundary:
                    part = link[0]
                    for sub in link[1]  :
                        face = part.getSubObject(sub)
                        if isinstance(face.Surface, Part.Plane):
                            shp = self.getOutsideCV(face, fp.TrimmedBody.Shape)
                            cut_shapes.append(shp)
        
        elif fp.CornerType == "End Miter":
            doc = App.activeDocument()
            precision = 0.001
            target1 = self.getTarget(fp.TrimmedBody)
            edge1 = doc.getObject(target1[0].Name).getSubObject(target1[1][0])
            bounds_target = []
            for bound in fp.TrimmingBoundary:
                bounds_target.append(self.getTarget(bound[0]))
            trimming_boundary_edges = []
            for target in bounds_target:
                trimming_boundary_edges.append(doc.getObject(target[0].Name).getSubObject(target[1][0]))
            for edge2 in trimming_boundary_edges:
                end1 = edge1.Vertexes[-1].Point
                start1 = edge1.Vertexes[0].Point
                end2 = edge2.Vertexes[-1].Point
                start2 = edge2.Vertexes[0].Point
                vec1 = start1.sub(end1)
                vec2 = start2.sub(end2)
                
                angle = math.degrees(vec1.getAngle(vec2))

                if end1.distanceToPoint(start2) < precision or start1.distanceToPoint(end2) < precision :
                    angle = 180-angle

                bisect = angle / 2.0

                if start1.distanceToPoint(start2) < precision :
                    p1 = start1
                    p2 = end1
                    p3 = end2
                elif start1.distanceToPoint(end2) < precision :
                    p1 = start1
                    p2 = end1
                    p3 = start2
                elif end1.distanceToPoint(start2) < precision :
                    p1 = end1
                    p2 = start1
                    p3 = end2
                elif end1.distanceToPoint(end2) < precision :
                    p1 = end1
                    p2 = start1
                    p3 = start2

                normal = Part.Plane(p1, p2, p3).toShape().normalAt(0,0)
                cutplane = Part.makePlane(10, 10, p1, vec1, normal)
                cutplane.rotate(p1, normal, -90+bisect)
                cut_shapes.append(self.getOutsideCV(cutplane, fp.TrimmedBody.Shape))
        
        if len(cut_shapes) > 0:
            cut_shape = Part.Shape(cut_shapes[0])
            for sh in cut_shapes[1:]:
                cut_shape = cut_shape.fuse(sh)
        
        self.makeShape(fp, cut_shape)

    def getOutsideCV(self, cutplane, shape):
        cv = ArchCommands.getCutVolume(cutplane, shape, clip=False, depth=0.0)
        if cv[1].isInside(shape.CenterOfGravity, 0.001, False):
            cv = cv[2]
        else:
            cv = cv[1]
        return cv

    def makeShape(self, fp, cutshape):
        if not cutshape.isNull():
            fp.Shape =  fp.TrimmedBody.Shape.cut(cutshape)
        else:
            #TODO: Do something when cutshape is Null
            print("cut_shape is Null")
        
    def getTarget(self, link):
        while True:
            if hasattr(link, "Target" ):
                return link.Target
            elif hasattr(link, "CornerType"):
                link = link.TrimmedBody
        

class ViewProviderCorner:
    def __init__(self, obj):
        ''' Set this object to the proxy object of the actual view provider '''
        obj.Proxy = self
    
    def attach(self, vobj):
        ''' Setup the scene sub-graph of the view provider, this method is mandatory '''
        self.ViewObject = vobj
        self.Object = vobj.Object
        return
        
    def updateData(self, fp, prop):
        ''' If a property of the handled feature has changed we have the chance to handle this here '''
        #App.Console.PrintMessage("Change {} property: {}\n".format(str(fp), str(prop)))
        if prop == "TrimmedBody":
            if fp.TrimmedBody:
                self.ViewObject.ShapeColor = fp.TrimmedBody.ViewObject.ShapeColor
        return
    
    def getDisplayModes(self, obj):
        ''' Return a list of display modes. '''
        modes=[]
        return modes
    
    def getDefaultDisplayMode(self):
        ''' Return the name of the default display mode. It must be defined in getDisplayModes. '''
        return "FlatLines"
    
    def setDisplayMode(self, mode):
        ''' Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done. This method is optional.
        '''
        return mode
    
    def claimChildren(self):
        childrens = [self.Object.TrimmedBody]
        if len(childrens) > 0:
            for child in childrens:
                if child:
                    #if hasattr("ViewObject", child)
                    child.ViewObject.Visibility = False
        return childrens
    
    def onChanged(self, vp, prop):
        ''' Print the name of the property that has changed '''
        #App.Console.PrintMessage("Change {} property: {}\n".format(str(vp), str(prop)))
        pass

    def onDelete(self, fp, sub):
        if self.Object.TrimmedBody:
            self.Object.TrimmedBody.ViewObject.Visibility = True
        return True
    
    def getIcon(self):
        ''' Return the icon in XMP format which will appear in the tree view. This method is optional
        and if not defined a default icon is shown.
        '''
        return """
        	/* XPM */
                static char * corner_xpm[] = {
                "16 16 4 1",
                " 	c None",
                ".	c #000000",
                "+	c #3465A4",
                "@	c #ED2B00",
                "         ..     ",
                "       ..++..   ",
                "   .....+++++.  ",
                " ..@@@@@.+++... ",
                " .@.@@@@@.+.++. ",
                " .@@.@...@.+++. ",
                " .@@@.@@@@.+++. ",
                " .@@@.@@@@.+++. ",
                " ..@@.@@@@....  ",
                " .+.@.@@...     ",
                " .++....++.     ",
                " .+++.++++.     ",
                " .+++.++++.     ",
                "  .++.++++.     ",
                "   .+.+...      ",
                "    ...         "};
        	"""

    def __getstate__(self):
        ''' When saving the document this object gets stored using Python's cPickle module.
        Since we have some un-pickable here -- the Coin stuff -- we must define this method
        to return a tuple of all pickable objects or None.
        '''
        return None
    
    def __setstate__(self,state):
        ''' When restoring the pickled object from document we have the chance to set some
        internals here. Since no data were pickled nothing needs to be done here.
        '''
        return None

    def setEdit(self, vobj, mode):
        if mode != 0:
            return None

        taskd = CornerTaskPanel(self.Object, mode="edition")
        Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if mode != 0:
            return None

        Gui.Control.closeDialog()
        return True

    def edit(self):
        FreeCADGui.ActiveDocument.setEdit(self.Object, 0)


class _CommandCorner:
    """This tool create a Draft Line based on the target of the prfile then activated Draft Trimex on it
    The difference between the target and the Draft Line allow us to add offset to profile object"""
    def __init__(self):
        pass

    def GetResources(self):
        "Tool resources"
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "corner.svg"),
            "MenuText": QT_TRANSLATE_NOOP("MetalWB", "Corner"),
            "Accel": "M, C",
            "ToolTip": QT_TRANSLATE_NOOP("MetalWB", "<html><head/><body><p><b>Create a corner</b> \
                    <br><br> \
                    Select a profile then another profile's faces. \
                    </p></body></html>"),
        }

    def IsActive(self):
        if App.ActiveDocument:
            if len(Gui.Selection.getSelection()) > 0:
                active = False
                for sel in Gui.Selection.getSelection():
                    if hasattr(sel, 'Target'):
                        active = True
                    elif hasattr(sel, 'TrimmedBody'):
                        active = True
                    else:
                        return False
                return active
            else:
                return True
        return False

    def Activated(self):
        """Define what happen when the user clic on the tool"""
        #doc = App.activeDocument()
        sel = Gui.Selection.getSelectionEx()
        App.ActiveDocument.openTransaction("Make Corner")
        if len(sel) == 0:
            corner = makeCorner()
        elif len(sel) == 1:
            corner = makeCorner(trimmedBody=sel[0].Object)
        elif len(sel) > 1 :
            trimmingboundary = []
            for selectionObject in sel[1:]:
                bound = (selectionObject.Object, selectionObject.SubElementNames)
                trimmingboundary.append(bound)
            corner = makeCorner(trimmedBody=sel[0].Object, trimmingBoundary=trimmingboundary)
        App.ActiveDocument.commitTransaction()
        App.CornerDialog = CornerTaskPanel(corner, mode="creation")
        Gui.Control.showDialog(App.CornerDialog)

class CornerTaskPanel():

    "A task panel for the survey tool"

    def __init__(self, fp, mode):
        self.fp = fp
        self.dump = fp.dumpContent()
        self.mode=mode
        self.form = QtGui.QWidget()
        icon = QtGui.QIcon(os.path.join(ICONPATH, "corner.svg"))
        add_icon = QtGui.QIcon(os.path.join(ICONPATH, "list-add.svg"))
        remove_icon = QtGui.QIcon(os.path.join(ICONPATH, "list-remove.svg"))
        endTrimIcon = QtGui.QIcon(os.path.join(ICONPATH, "corner-end-trim.svg"))
        endMiterIcon = QtGui.QIcon(os.path.join(ICONPATH, "corner-end-miter.svg"))
        copedTypeIcon = QtGui.QIcon(os.path.join(ICONPATH, "corner-coped-type.svg"))
        simpleTypeIcon = QtGui.QIcon(os.path.join(ICONPATH, "corner-simple-type.svg"))
        p = App.ParamGet("User parameter:BaseApp/Preferences/General")
        iconSize = p.GetInt("ToolbarIconSize") * 1.5
        iconQSize = QtCore.QSize(iconSize, iconSize)
        minimumQSize = QtCore.QSize(int(iconSize*1.2), int(iconSize*1.2))
        self.form.setWindowIcon(icon)
        layout = QtGui.QVBoxLayout(self.form)

        self.cornerTypeLabel = QtGui.QLabel()
        layout.addWidget(self.cornerTypeLabel)

        llayout = QtGui.QHBoxLayout()

        self.endTrimButton = QtGui.QPushButton()
        self.endTrimButton.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.endTrimButton.setMinimumSize(minimumQSize)
        self.endTrimButton.setIcon(endTrimIcon)
        self.endTrimButton.setIconSize(iconQSize)
        self.endTrimButton.setCheckable(True)
        self.endTrimButton.setChecked(True)

        llayout.addWidget(self.endTrimButton)

        self.endMiterButton = QtGui.QPushButton()
        self.endMiterButton.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.endMiterButton.setMinimumSize(minimumQSize)
        self.endMiterButton.setIcon(endMiterIcon)
        self.endMiterButton.setIconSize(iconQSize)
        self.endMiterButton.setCheckable(True)
        llayout.addWidget(self.endMiterButton)
        llayout.addStretch()
        layout.addLayout(llayout)

        layoutTrimmedBody = QtGui.QHBoxLayout()
        self.trimmedBodyLabel = QtGui.QLabel()
        layoutTrimmedBody.addWidget(self.trimmedBodyLabel)
        self.addTrimmedBodyButton = QtGui.QPushButton()
        self.addTrimmedBodyButton.setIcon(add_icon)
        layoutTrimmedBody.addWidget(self.addTrimmedBodyButton)
        self.removeTrimmedBodyButton = QtGui.QPushButton()
        self.removeTrimmedBodyButton.setIcon(remove_icon)
        layoutTrimmedBody.addWidget(self.removeTrimmedBodyButton)
        layoutTrimmedBody.addStretch()
        layout.addLayout(layoutTrimmedBody)

        self.trimmedBodyListWidget = QtGui.QListWidget()
        self.trimmedBodyListWidget.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        layout.addWidget(self.trimmedBodyListWidget)

        layoutTrimmingBodies = QtGui.QHBoxLayout()
        self.trimmingBodiesLabel = QtGui.QLabel()
        layoutTrimmingBodies.addWidget(self.trimmingBodiesLabel)
        self.addTrimmingBodiesButton = QtGui.QPushButton()
        self.addTrimmingBodiesButton.setIcon(add_icon)
        layoutTrimmingBodies.addWidget(self.addTrimmingBodiesButton)
        self.removeTrimmingBodiesButton = QtGui.QPushButton()
        self.removeTrimmingBodiesButton.setIcon(remove_icon)
        layoutTrimmingBodies.addWidget(self.removeTrimmingBodiesButton)
        layoutTrimmingBodies.addStretch()
        layout.addLayout(layoutTrimmingBodies)

        self.trimmingBodiesListWidget = QtGui.QListWidget()
        layout.addWidget(self.trimmingBodiesListWidget)

        self.cutTypeLabel = QtGui.QLabel()
        layout.addWidget(self.cutTypeLabel)

        blayout = QtGui.QHBoxLayout()
        self.copedCutTypeButton = QtGui.QPushButton()
        self.copedCutTypeButton.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.copedCutTypeButton.setMinimumSize(minimumQSize)
        self.copedCutTypeButton.setIcon(copedTypeIcon)
        self.copedCutTypeButton.setIconSize(iconQSize)
        self.copedCutTypeButton.setCheckable(True)
        self.copedCutTypeButton.setChecked(True)

        self.simpleCutTypeButton = QtGui.QPushButton()
        self.simpleCutTypeButton.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.simpleCutTypeButton.setMinimumSize(minimumQSize)
        self.simpleCutTypeButton.setIcon(simpleTypeIcon)
        self.simpleCutTypeButton.setIconSize(iconQSize)
        self.simpleCutTypeButton.setCheckable(True)

        blayout.addWidget(self.copedCutTypeButton)
        blayout.addWidget(self.simpleCutTypeButton)
        blayout.addStretch()
        layout.addLayout(blayout)

        QtCore.QObject.connect(self.endTrimButton, QtCore.SIGNAL("clicked()"), self.endTrimButtonClicked)
        QtCore.QObject.connect(self.endMiterButton, QtCore.SIGNAL("clicked()"), self.endMiterButtonClicked)
        QtCore.QObject.connect(self.copedCutTypeButton, QtCore.SIGNAL("clicked()"), self.copedCutTypeButtonClicked)
        QtCore.QObject.connect(self.simpleCutTypeButton, QtCore.SIGNAL("clicked()"), self.simpleCutTypeButtonClicked)
        QtCore.QObject.connect(self.addTrimmedBodyButton, QtCore.SIGNAL("clicked()"), self.addTrimmedBody)
        QtCore.QObject.connect(self.removeTrimmedBodyButton, QtCore.SIGNAL("clicked()"), self.removeTrimmedBody)
        QtCore.QObject.connect(self.addTrimmingBodiesButton, QtCore.SIGNAL("clicked()"), self.addTrimmingBodies)
        QtCore.QObject.connect(self.removeTrimmingBodiesButton, QtCore.SIGNAL("clicked()"), self.removeTrimmingBodies)
        self.retranslateUi(self)
        self.updateUi()

    def retranslateUi(self, dlg):
        self.form.setWindowTitle(QtGui.QApplication.translate("MetalWB", "Corner Manager", None))
        self.cornerTypeLabel.setText(QtGui.QApplication.translate("MetalWB", "Corner type", None))
        self.endTrimButton.setToolTip(QtGui.QApplication.translate("MetalWB", "End trim"))
        self.endMiterButton.setToolTip(QtGui.QApplication.translate("MetalWB", "End miter"))
        self.trimmedBodyLabel.setText(QtGui.QApplication.translate("MetalWB", "Trimmed body", None))
        self.addTrimmedBodyButton.setToolTip(QtGui.QApplication.translate("MetalWB", "Set selected object to trimmed body"))
        self.removeTrimmedBodyButton.setToolTip(QtGui.QApplication.translate("MetalWB", "Remove trimmed body"))
        self.trimmingBodiesLabel.setText(QtGui.QApplication.translate("MetalWB", "Trimming boundary", None))
        self.addTrimmingBodiesButton.setToolTip(QtGui.QApplication.translate("MetalWB", "Add selected object to trimming boundary"))
        self.removeTrimmingBodiesButton.setToolTip(QtGui.QApplication.translate("MetalWB", "Remove selected object from trimming boundary"))
        self.cutTypeLabel.setText(QtGui.QApplication.translate("MetalWB", "Cut type", None))

    def updateUi(self):
        if self.fp.CornerType == u"End Trim":
            self.endTrimButton.setChecked(True)
            self.endTrimButtonClicked(update=True)

        if self.fp.CornerType == u"End Miter":
            self.endMiterButton.setChecked(True)
            self.endMiterButtonClicked(update=True)

        if self.fp.CutType == u"Coped cut":
            self.copedCutTypeButton.setChecked(True)
            self.copedCutTypeButtonClicked(update=True)

        if self.fp.CutType == u"Simple cut":
            self.simpleCutTypeButton.setChecked(True)
            self.simpleCutTypeButtonClicked(update=True)

        if self.fp.TrimmedBody:
            self.trimmedBodyListWidget.clear()
            label = self.fp.TrimmedBody.Label
            name = self.fp.TrimmedBody.Name
            item_str = "{} ({})".format(label, name)
            item_data = self.fp.TrimmedBody
            item = QtGui.QListWidgetItem()
            item.setText(item_str)
            item.setData(1, item_data)
            self.trimmedBodyListWidget.addItem(item)
        else:
            self.trimmedBodyListWidget.clear()
            pass

        if self.fp.TrimmingBoundary:
            self.trimmingBodiesListWidget.clear()
            for bound in self.fp.TrimmingBoundary:
                label = bound[0].Label
                name = bound[0].Name
                sub_str = str()
                for sub in bound[1]:
                    sub_str += str(sub)
                    sub_str += ','
                item_str = "{} ({} {})".format(label, name, sub_str)
                item_data = bound[0]
                item = QtGui.QListWidgetItem()
                item.setText(item_str)
                item.setData(1, item_data)
                self.trimmingBodiesListWidget.addItem(item)
        else:
            self.trimmingBodiesListWidget.clear()


    def endTrimButtonClicked(self, update=False):
        if self.endTrimButton.isChecked() is True:
            self.endMiterButton.setChecked(False)
            self.simpleCutTypeButton.setEnabled(True)
            self.copedCutTypeButton.setEnabled(True)
            if update is False:
                self.fp.CornerType = u"End Trim"
                self.fp.recompute()
                self.updateUi()

    def endMiterButtonClicked(self, update=False):
        if self.endMiterButton.isChecked() is True:
            self.endTrimButton.setChecked(False)
            self.simpleCutTypeButton.setEnabled(False)
            self.copedCutTypeButton.setEnabled(False)
            if update is False:
                self.fp.CornerType = u"End Miter"
                self.fp.recompute()
                self.updateUi()

    def copedCutTypeButtonClicked(self, update=False):
        if self.copedCutTypeButton.isChecked() is True:
            self.simpleCutTypeButton.setChecked(False)
            if update is False:
                self.fp.CutType = u"Coped cut"
                self.fp.recompute()
                self.updateUi()

    def simpleCutTypeButtonClicked(self, update=False):
        if self.simpleCutTypeButton.isChecked() is True:
            self.copedCutTypeButton.setChecked(False)
            if update is False:
                self.fp.CutType = u"Simple cut"
                self.fp.recompute()
                self.updateUi()

    def addTrimmedBody(self):
        if self.trimmedBodyListWidget.count() == 0:
            if len(Gui.Selection.getSelectionEx()) == 1:
                print(Gui.Selection.getSelection())
                self.fp.TrimmedBody = Gui.Selection.getSelectionEx()[0].Object
                self.fp.recompute()
                self.updateUi()

    def removeTrimmedBody(self):
        self.fp.TrimmedBody = None
        self.fp.recompute()
        self.updateUi()

    def addTrimmingBodies(self):
        doc = App.ActiveDocument
        newTrimingBoundary = []
        existingTrimmingBoundaryNames = []
        for partObject in self.fp.TrimmingBoundary:
            existingTrimmingBoundaryNames.append(partObject[0].Name)

        selectionTrimmingBoundaryNames = []
        for selectionObject in Gui.Selection.getSelectionEx():
            selectionTrimmingBoundaryNames.append(selectionObject.Object.Name)

        newTrimingBoundaryNames = existingTrimmingBoundaryNames + list(set(selectionTrimmingBoundaryNames) - set(existingTrimmingBoundaryNames))
        for boundaryPartName in newTrimingBoundaryNames:
            subFp = []
            subSel = []
            for partObject in self.fp.TrimmingBoundary:
                if partObject[0].Name == boundaryPartName:
                    for s in partObject[1]:
                        subFp.append(s)
            for partObject in Gui.Selection.getSelectionEx():
                if partObject.Object.Name == boundaryPartName:
                    for s in selectionObject.SubElementNames:
                        subSel.append(s)
            sub = subFp + list(set(subSel) - set(subFp))
            partObject = doc.getObject(boundaryPartName)
            newTrimingBoundary.append((partObject, tuple(sub)))
        self.fp.TrimmingBoundary = newTrimingBoundary  
        self.fp.recompute()
        self.updateUi()


    def removeTrimmingBodies(self):
        print(self.trimmingBodiesListWidget.selectedItems())
        items = self.trimmingBodiesListWidget.selectedItems()
        boundary = self.fp.TrimmingBoundary
        for item in items:
            print(item.text())
            print(item.data(1))
            idx = 0
            for bound in boundary:
                if bound[0].Name == item.data(1).Name:
                    boundary.pop(idx)
                    idx += 1
        self.fp.TrimmingBoundary = boundary  
        self.fp.recompute()
        self.updateUi()

    def accept(self):
        """This method runs as a callback when the user selects the ok button.

        Recomputes the document, and leave edit mode.
        """

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()
        return True

    def reject(self):
        """This method runs as a callback when the user selects the ok button.

        Recomputes the document, and leave edit mode.
        """
        if self.mode == "edition":
            self.fp.restoreContent(self.dump)
            Gui.ActiveDocument.resetEdit()
        elif self.mode == "creation":
            trimmedBody = self.fp.TrimmedBody
            App.ActiveDocument.removeObject(self.fp.Name)
            if trimmedBody:
                trimmedBody.ViewObject.Visibility = True
        App.ActiveDocument.recompute()
        return True



if App.GuiUp:
    Gui.addCommand("MetalWB_Corner", _CommandCorner())