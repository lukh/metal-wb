# -*- coding: utf-8 -*-

__title__ = "Split curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Splits the selected edge"
__usage__ = """Select an edge in the 3D View, or an object containing a wire in the Tree View
Activate Tool
The selected edges (or wire) will be cut at the specified location.
The split locations can be given as real edge parameter, absolute distance(mm) or relative distance (%)
The split locations can be set by proximity to cutting objects.
Double-click in Tree-View to toggle Freehand editor in 3D View.
"""


import os
import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui

from freecad.metalwb import _utils
from freecad.metalwb import ICONPATH
from freecad.metalwb.nurbs_tools import KnotVector

from pivy import coin
from freecad.metalwb import graphics


TOOL_ICON = os.path.join(ICONPATH, 'splitcurve.svg')
# debug = _utils.debug
debug = _utils.doNothing


class split:
    """Splits the selected edge."""
    def __init__(self, obj, e):
        obj.Proxy = self
        obj.addProperty("App::PropertyLinkSub",
                        "Source",
                        "Base",
                        "Edge to split").Source = e
        obj.addProperty("App::PropertyStringList",
                        "Values",
                        "Split",
                        "List of splitting locations\n% and units are allowed\nNegative values are computed from edge end")
        obj.addProperty("App::PropertyLinkList",
                        "CuttingObjects",
                        "Split",
                        "List of objects that cut the curve")
        obj.addProperty("App::PropertyDistance",
                        "Distance",
                        "Split",
                        "Expression-ready distance value")
        obj.addProperty("App::PropertyFloatList",
                        "NormalizedParameters",
                        "Output",
                        "Normalized parameters list")
        obj.setEditorMode("NormalizedParameters", 2)

    def getShape(self, fp):
        if fp.Source is None:
            return None, None
        if fp.Source[1] == []:  # No subshape given, take wire 1
            if fp.Source[0].Shape.Wires:
                w = fp.Source[0].Shape.Wire1
                e = w.approximate(1e-7, 1e-5, len(w.Edges), 7).toShape()
                # double tol2d = gp::Resolution();
                # double tol3d = 0.0001;
                # int maxseg=10, maxdeg=3;
                # static char* kwds_approx[] = {"Tol2d","Tol3d","MaxSegments","MaxDegree",NULL};
            else:
                return None, None
        else:
            e = _utils.getShape(fp, "Source", "Edge")
            w = False
        return e, w

    def parse_value(self, edge, v):
        num_val = None
        par = None
        if v == '':
            return None, None
        elif "%" in v:
            num_val = float(v.split("%")[0]) * edge.Length / 100
            t = '%'
        else:
            num_val = App.Units.parseQuantity(v).Value
            t = App.Units.Unit(v).Type
        if t == '':
            par = num_val
        elif num_val < 0:
            par = edge.Curve.parameterAtDistance(num_val, edge.LastParameter)
        else:
            par = edge.Curve.parameterAtDistance(num_val, edge.FirstParameter)
        if par > edge.FirstParameter and par < edge.LastParameter:
            return par, t
        return None, None

    def parse_values(self, edge, values):
        # edge = self.getShape(fp, "Source", "Edge")
        if not edge:
            return
        parameters = []
        for v in values:
            par, t = self.parse_value(edge, v)
            if par:
                parameters.append(par)
        parameters.sort()
        return parameters

    def onChanged(self, fp, prop):
        e = None
        if hasattr(fp, "Source") and fp.Source:
            e, w = self.getShape(fp)
        if not e:
            return
        if prop in ["Source", "Values", "Distance", "CuttingObjects"]:
            debug("Split : {} changed".format(prop))
            self.execute(fp)

    def execute(self, obj):
        e, w = self.getShape(obj)
        if not isinstance(e, Part.Edge):
            return
        val = []
        if hasattr(obj, "Values"):
            val = obj.Values
        if hasattr(obj, "Distance"):
            val.append(obj.Distance.toStr())
        params = []
        if val:
            params = self.parse_values(e, val)
        if hasattr(obj, "CuttingObjects"):
            for o in obj.CuttingObjects:
                d, pts, info = e.distToShape(o.Shape)
                for inf in info:
                    if inf[0] == 'Edge':
                        debug('adding param : {}'.format(inf[2]))
                        params.append(inf[2])

        if params == []:
            if w:
                obj.Shape = obj.Source[0].Shape
            else:
                obj.Shape = e
            return

        params.sort()
        if params[0] > e.FirstParameter:
            params.insert(0, e.FirstParameter)
        if params[-1] < e.LastParameter:
            params.append(e.LastParameter)

        if w:  # No subshape given, take wire 1
            edges = w.Edges
            for i in range(len(params)):
                p = e.valueAt(params[i])
                d, pts, info = Part.Vertex(p).distToShape(w)
                # print(info)
                if info[0][3] == "Edge":
                    n = info[0][4]
                    nw = w.Edges[n].split(info[0][5])
                    nw.Placement = w.Edges[n].Placement
                    if len(nw.Edges) == 2:
                        edges[n] = nw.Edges[0]
                        edges.insert(n + 1, nw.Edges[1])

                        # print([e.Length for e in edges])
                        se = Part.sortEdges(edges)
                        if len(se) > 1:
                            App.Console.PrintError("Split curve : failed to build temp Wire !")
                            # print(se)
                        w = Part.Wire(se[0])
        else:
            edges = []
            print(params)
            for i in range(len(params) - 1):
                c = e.Curve.trim(params[i], params[i + 1])
                edges.append(c.toShape())

        se = Part.sortEdges(edges)
        if len(se) > 1:
            App.Console.PrintError("Split curve : failed to build final Wire !")
            wires = []
            for el in se:
                wires.append(Part.Wire(el))
            w = Part.Compound(wires)
        else:
            w = Part.Wire(se[0])
        if w.isValid():
            obj.Shape = w
            obj.NormalizedParameters = KnotVector(params).normalize()
        else:
            App.Console.PrintError("Split curve : Invalid Wire !")
            obj.Shape = e


class MarkerOnEdge(graphics.Marker):
    def __init__(self, points, sh=None):
        super(MarkerOnEdge, self).__init__(points, True)
        self._shape = None
        self._sublink = None
        self._tangent = None
        self._text_type = 0
        self._text_translate = coin.SoTranslation()
        self._text_font = coin.SoFont()
        self._text_font.name = "Arial:Bold"
        self._text_font.size = 13.0
        self._text = coin.SoText2()
        self._text_switch = coin.SoSwitch()
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
        self._text_switch.addChild(self._text_translate)
        self._text_switch.addChild(self._text_font)
        self._text_switch.addChild(self._text)
        # self.on_drag_start.append(self.add_text)
        # self.on_drag_release.append(self.remove_text)
        self.on_drag.append(self.update_text)
        self.update_text()
        self.addChild(self._text_switch)

        if isinstance(sh, Part.Shape):
            self.snap_shape = sh
        elif isinstance(sh, (tuple, list)):
            self.sublink = sh

    def subshape_from_sublink(self, o):
        name = o[1][0]
        if 'Vertex' in name:
            n = eval(name.lstrip('Vertex'))
            return(o[0].Shape.Vertexes[n - 1])
        elif 'Edge' in name:
            n = eval(name.lstrip('Edge'))
            return(o[0].Shape.Edges[n - 1])
        elif 'Face' in name:
            n = eval(name.lstrip('Face'))
            return(o[0].Shape.Faces[n - 1])

    def add_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_ALL
        self.on_drag.append(self.update_text)

    def remove_text(self):
        self._text_switch.whichChild = coin.SO_SWITCH_NONE
        self.on_drag.remove(self.update_text)

    def update_text(self):
        if self._shape is None:
            return
        p = self.points[0]
        par = self._shape.Curve.parameter(App.Vector(p[0], p[1], p[2]))
        if self._text_type == 0:
            coords = ['{: 9.3f}'.format(par)]
        else:
            if par <= self._shape.FirstParameter:
                abscissa = 0
            else:
                c = self._shape.Curve.trim(self._shape.FirstParameter, par)
                abscissa = c.length()
            if self._text_type == 1:
                coords = ['{: 9.3f} mm'.format(abscissa)]
            elif self._text_type == 2:
                perc = 100 * abscissa / self._shape.Length
                coords = ['{: 9.3f} %'.format(perc)]
        self._text_translate.translation = p
        self._text.string.setValues(0, len(coords), coords)

    @property
    def tangent(self):
        return self._tangent

    @tangent.setter
    def tangent(self, t):
        if isinstance(t, App.Vector):
            if t.Length > 1e-7:
                self._tangent = t
                self._tangent.normalize()
                self.marker.markerIndex = coin.SoMarkerSet.DIAMOND_FILLED_9_9
            else:
                self._tangent = None
                self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
        else:
            self._tangent = None
            self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9

    @property
    def snap_shape(self):
        return self._shape

    @snap_shape.setter
    def snap_shape(self, sh):
        if isinstance(sh, Part.Shape):
            self._shape = sh
        else:
            self._shape = None
        # self.alter_color()

    @property
    def sublink(self):
        return self._sublink

    @sublink.setter
    def sublink(self, sl):
        if isinstance(sl, (tuple, list)) and not (sl == self._sublink):
            self._shape = self.subshape_from_sublink(sl)
            self._sublink = sl
        else:
            self._shape = None
            self._sublink = None
        # self.alter_color()

    def alter_color(self):
        if isinstance(self._shape, Part.Vertex):
            self.set_color("white")
        elif isinstance(self._shape, Part.Edge):
            self.set_color("cyan")
        elif isinstance(self._shape, Part.Face):
            self.set_color("magenta")
        else:
            self.set_color("black")

    def __repr__(self):
        return "MarkerOnShape({})".format(self._shape)

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, p in enumerate(pts):
                p[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                p[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                p[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
                if self._shape:
                    v = Part.Vertex(p[0], p[1], p[2])
                    proj = v.distToShape(self._shape)[1][0][1]
                    # App.Console.PrintMessage("%s -> %s\n"%(p.getValue(),proj))
                    p[0] = proj.x
                    p[1] = proj.y
                    p[2] = proj.z
            self.points = pts
            for foo in self.on_drag:
                foo()


class pointEditor(object):
    """Free-hand editor
    my_editor = pointEditor([points],obj)
    obj is the FreeCAD object that will receive
    the curve shape at the end of editing.
    points can be :
    - Vector (free point)
    - (Vector, shape) (point on shape)"""
    def __init__(self, points=[], fp=None):
        self.points = list()
        self.fp = fp
        self.curve = None
        self.root_inserted = False
        self.ctrl_keys = {"i": [self.insert],
                          "v": [self.text_change],
                          "q": [self.quit],
                          "\uffff": [self.remove_point]}
        for p in points:
            if isinstance(p, App.Vector):
                self.points.append(MarkerOnEdge(p))
            elif isinstance(p, (tuple, list)):
                self.points.append(MarkerOnEdge(p[0], p[1]))
            elif isinstance(p, MarkerOnEdge):
                self.points.append(p)
            else:
                App.Console.PrintError("pointEditor : bad input")
        for p in points:
            if hasattr(p, "ctrl_keys"):
                for key in p.ctrl_keys:
                    if key in self.ctrl_keys:
                        # print(key)
                        self.ctrl_keys[key].extend(p.ctrl_keys[key])
                    else:
                        self.ctrl_keys[key] = p.ctrl_keys[key]

        # Setup coin objects
        if self.fp:
            self.guidoc = self.fp.ViewObject.Document
        else:
            if not Gui.ActiveDocument:
                App.newDocument("New")
        self.guidoc = Gui.ActiveDocument
        self.view = self.guidoc.ActiveView
        self.rm = self.view.getViewer().getSoRenderManager()
        self.sg = self.view.getSceneGraph()
        self.setup_InteractionSeparator()

    def setup_InteractionSeparator(self):
        if self.root_inserted:
            self.sg.removeChild(self.root)
        self.root = graphics.InteractionSeparator(self.rm)
        self.root.setName("InteractionSeparator")
        # self.root.ovr_col = "yellow"
        # self.root.sel_col = "green"
        self.root.pick_radius = 40
        # self.root.on_drag.append(self.update_curve)
        # Keyboard callback
        # self.events = coin.SoEventCallback()
        self._controlCB = self.root.events.addEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self.controlCB)
        # populate root node
        # self.root.addChild(self.events)
        self.root += self.points
        # self.root += self.lines
        # set FreeCAD color scheme
        for o in self.points:  # + self.lines:
            o.ovr_col = "yellow"
            o.sel_col = "green"
        self.root.register()
        self.sg.addChild(self.root)
        self.root_inserted = True
        self.root.selected_objects = list()

    def controlCB(self, attr, event_callback):
        event = event_callback.getEvent()
        if event.getState() == event.UP:
            # App.Console.PrintMessage("Key pressed : %s\n"%event.getKey())
            if chr(event.getKey()) in self.ctrl_keys:
                for foo in self.ctrl_keys[chr(event.getKey())]:
                    if foo.__self__ is self:
                        foo()
                    elif foo.__self__.parent in self.root.selected_objects:
                        foo()

    def remove_point(self):
        pts = list()
        for o in self.root.dynamic_objects:
            if isinstance(o, MarkerOnEdge):
                pts.append(o)
        self.points = pts
        self.setup_InteractionSeparator()

    def insert(self):
        # get selected lines and subdivide them
        # pts = []
        for o in self.root.selected_objects:
            # p1 = o.points[0]
            mark = MarkerOnEdge(o.points, o.snap_shape)
            self.points.append(mark)
            # new_select.append(mark)
        # self.points.append(pts)
        self.setup_InteractionSeparator()
        # self.root.selected_objects = new_select
        return True

    def text_change(self):
        for o in self.root.selected_objects:
            if o._text_type == 2:
                o._text_type = 0
            else:
                o._text_type += 1

    def quit(self):
        self.root.events.removeEventCallback(coin.SoKeyboardEvent.getClassTypeId(), self._controlCB)
        self.root.unregister()
        # self.root.removeAllChildren()
        self.sg.removeChild(self.root)
        self.root_inserted = False


class splitVP:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.select_state = True
        self.active = False
        self.ps = 0.0

    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ip = None
        self.ps = 0.0

    def setEdit(self, vobj, mode=0):
        if mode == 0:
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
                self.ps = vobj.PointSize
                vobj.PointSize = 0.0
            # sl = self.Object.Source
            e, w = self.Object.Proxy.getShape(self.Object)
            params = []
            if hasattr(self.Object, "Values"):
                params = self.Object.Proxy.parse_values(e, self.Object.Values)
            if params == []:
                return False
            pts = list()
            # print("Creating markers")
            if hasattr(self.Object, "Values"):
                for v in self.Object.Values:
                    p, t = self.Object.Proxy.parse_value(e, v)
                    # print("{} -> {}".format(p, e.valueAt(p)))
                    m = MarkerOnEdge([e.valueAt(p)], e)
                    if t == '':
                        m._text_type = 0
                    elif t == '%':
                        m._text_type = 2
                    else:
                        m._text_type = 1
                    # m = manipulators.EdgeSnapAndTangent(e.valueAt(p), e)
                    pts.append(m)
            # print(pts)
            self.ip = pointEditor(pts, self.Object)
            # self.ip.curve = e.Curve
            # vobj.Visibility = False
            self.active = True
            # print("Edit setup OK")
            return True
        return False

    def unsetEdit(self, vobj, mode=0):
        e, w = self.Object.Proxy.getShape(self.Object)
        if isinstance(self.ip, pointEditor):
            params = list()
            for p in self.ip.points:
                if isinstance(p, MarkerOnEdge):
                    pt = p.points[0]
                    par = e.Curve.parameter(App.Vector(pt))
                    temp = e.Curve.trim(e.FirstParameter, par)
                    # value = p._text.string.getValues()[0]
                    # print(value)
                    if p._text_type == 0:
                        value = str(par)
                    elif p._text_type == 1:
                        value = "{:.3f}mm".format(temp.length())
                    elif p._text_type == 2:
                        value = "{:.3f}%".format(100 * temp.length() / e.Length)
                    params.append(value)
            self.Object.Values = params
            vobj.Selectable = self.select_state
            vobj.PointSize = self.ps
            self.ip.quit()
        self.ip = None
        self.active = False
        # vobj.Visibility = True
        self.Object.Document.recompute()
        return True

    def doubleClicked(self, vobj):
        if not hasattr(self, 'active'):
            self.active = False
        if not self.active:
            self.active = True
            # self.setEdit(vobj)
            vobj.Document.setEdit(vobj)
        else:
            vobj.Document.resetEdit()
            self.active = False
        return True

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = App.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        if self.Object.Source:
            return [self.Object.Source[0]]

    def onDelete(self, feature, subelements):
        if self.Object.Source and hasattr(self.Object.Source[0], "ViewObject"):
            self.Object.Source[0].ViewObject.Visibility = True
        return True


class splitCommand:
    """Splits the selected edges."""
    def makeSplitFeature(self, e):
        splitCurve = App.ActiveDocument.addObject("Part::FeaturePython", "SplitCurve")
        split(splitCurve, e)
        splitVP(splitCurve.ViewObject)
        App.ActiveDocument.recompute()
        splitCurve.Values = ["50%"]
        splitCurve.ViewObject.PointSize = 5.0

    def Activated(self):
        sel = Gui.Selection.getSelectionEx()
        if sel == []:
            App.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Edge):
                        self.makeSplitFeature((selobj.Object, selobj.SubElementNames[i]))
                        if selobj.Object.Shape:
                            if len(selobj.Object.Shape.Edges) == 1:
                                selobj.Object.ViewObject.Visibility = False
            else:
                self.makeSplitFeature((selobj.Object, []))
                if hasattr(selobj.Object, "ViewObject"):
                    selobj.Object.ViewObject.Visibility = False

    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


Gui.addCommand('MetalWB_SplitCurves', splitCommand())
