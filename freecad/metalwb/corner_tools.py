# coding: utf-8

import FreeCAD as App
import Part, ArchCommands
import BOPTools.SplitAPI
import os
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



def makeCorner():
    doc = App.ActiveDocument
    corner = doc.addObject("Part::FeaturePython","Corner")
    Corner(corner)
    ViewProviderCorner(corner.ViewObject)
    sel = Gui.Selection.getSelectionEx()
    corner.TrimmedBody = sel[0].Object
    trimmingboundary = []
    for selectionObject in sel[1:]:
        bound = (selectionObject.Object, selectionObject.SubElementNames)
        trimmingboundary.append(bound)
        corner.TrimmingBoundary = trimmingboundary
    doc.recompute()
    return corner


class Corner:
    def __init__(self, obj):
        ''' Add some custom properties to our box feature '''
        obj.addProperty("App::PropertyLink","TrimmedBody","Corner","Bodies to be Trimmed").TrimmedBody=None
        obj.addProperty("App::PropertyLinkSubList","TrimmingBoundary","Corner","Trimming boundary").TrimmingBoundary=None
        #corner_types = ["End Trim", "End Miter", "End Butt1", "End Butt2",]
        corner_types = ["End Trim", "End Miter",]
        obj.addProperty("App::PropertyEnumeration","CornerType","Corner", "Corner Type").CornerType=corner_types
        cut_types = ["Coped cut", "Simple cut",]
        obj.addProperty("App::PropertyEnumeration","CutType","Corner", "Cut Type").CutType=cut_types
        obj.Proxy = self

    def onChanged(self, fp, prop):
        ''' Print the name of the property that has changed '''
        #App.Console.PrintMessage("Change property: " + str(prop) + "\n")
        pass

    def execute(self, fp):
        ''' Print a short message when doing a recomputation, this method is mandatory '''
        App.Console.PrintMessage("Recompute {}\n".format(fp.Name))
        #TODO: Put these methods in proper functions
        if fp.CornerType == "End Trim":
            #print("Corner Type == End Trim")
            if fp.CutType == "Coped cut":
                #print("Cut Type == Coped cut")
                shapes = [x[0].Shape for x in fp.TrimmingBoundary]
                shps = BOPTools.SplitAPI.slice(fp.TrimmedBody.Shape, shapes, mode="Split")
                cut_shape = Part.Shape()
                for solid in shps.Solids:
                    x = fp.TrimmedBody.Shape.CenterOfGravity.x
                    y = fp.TrimmedBody.Shape.CenterOfGravity.y
                    z = fp.TrimmedBody.Shape.CenterOfGravity.z
                    if not solid.BoundBox.isInside(x, y, z):
                        cut_shape = cut_shape.fuse(solid)
            elif fp.CutType == "Simple cut":
                #print("Cut Type == Simple cut")
                cut_shape = Part.Shape()
                for link in fp.TrimmingBoundary:
                    part = link[0]
                    for sub in link[1]  :
                        face = part.getSubObject(sub)
                        if isinstance(face.Surface, Part.Plane):
                            shp = self.getOutsideCV(face, fp.TrimmedBody.Shape)
                            cut_shape = cut_shape.fuse(shp)
            self.makeShape(fp, cut_shape)
        
        elif fp.CornerType == "End Miter":
            #print("Corner Type == End Miter")
            doc = App.activeDocument()
            target1 = self.getTarget(fp.TrimmedBody)
            edge1 = doc.getObject(target1[0].Name).getSubObject(target1[1][0])
            bounds_target = []
            for bound in fp.TrimmingBoundary:
                bounds_target.append(self.getTarget(bound[0]))
            trimming_boundary_edges = []
            for target in bounds_target:
                trimming_boundary_edges.append(doc.getObject(target[0].Name).getSubObject(target[1][0]))
            cut_shape = Part.Shape()
            for edge2 in trimming_boundary_edges:
                end1 = edge1.Vertexes[-1].Point
                start1 = edge1.Vertexes[0].Point
                end2 = edge2.Vertexes[-1].Point
                start2 = edge2.Vertexes[0].Point
                vec1 = start1.sub(end1)
                vec2 = start2.sub(end2)
                
                angle = math.degrees(vec1.getAngle(vec2))

                if end1 == start2 or start1 == end2 :
                    angle = 180-angle
                bisect = angle / 2.0

                if start1 == start2 :
                    p1 = start1
                    p2 = end1
                    p3 = end2
                elif start1 == end2:
                    p1 = start1
                    p2 = end1
                    p3 = start2
                elif end1 == start2:
                    p1 = end1
                    p2 = start1
                    p3 = end2
                elif end1 == end2:
                    p1 = end1
                    p2 = start1
                    p3 = start2

                normal = Part.Plane(p1, p2, p3).toShape().normalAt(0,0)
                cutplane = Part.makePlane(10, 10, p1, vec1, normal)
                cutplane.rotate(p1, normal, -90+bisect)
                cut_shape = cut_shape.fuse(self.getOutsideCV(cutplane, fp.TrimmedBody.Shape))
            self.makeShape(fp, cut_shape)

    def getOutsideCV(self, cutplane, shape):
        cv = ArchCommands.getCutVolume(cutplane, shape, clip=False, depth=0.0)
        #print("cv : ", cv)
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
        for child in childrens:
            child.ViewObject.Visibility = False
        return childrens
    
    def onChanged(self, vp, prop):
        ''' Print the name of the property that has changed '''
        #App.Console.PrintMessage("Change {} property: {}\n".format(str(vp), str(prop)))
        pass

    def onDelete(self, fp, sub):
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


class _CommandCorner:
    """This tool create a Draft Line based on the target of the prfile then activated Draft Trimex on it
    The difference between the target and the Draft Line allow us to add offset to profile object"""
    def __init__(self):
        pass

    def GetResources(self):
        "Tool resources"
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "overlap.svg"),
            "MenuText": QT_TRANSLATE_NOOP("MetalWB", "MetalWB_Corner"),
            "Accel": "M, C",
            "ToolTip": "<html><head/><body><p><b>Create a corner</b> \
                    <br><br> \
                    Select a profile then another profile's faces. \
                    </p></body></html>",
        }

    def IsActive(self):
        if App.ActiveDocument:
            if len(Gui.Selection.getSelection()) > 1:
                active = False
                for sel in Gui.Selection.getSelection():
                    if hasattr(sel, 'Target'):
                        active = True
                    elif hasattr(sel, 'TrimmedBody'):
                        active = True
                    else:
                        return False
                return active
        return False

    def Activated(self):
        """Define what happen when the user clic on the tool"""
        doc = App.activeDocument()
        corner = makeCorner()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(doc.Name, corner.Name)



if App.GuiUp:
    Gui.addCommand("MetalWB_Corner", _CommandCorner())