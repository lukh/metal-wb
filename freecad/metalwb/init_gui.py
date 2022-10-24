
import os
import FreeCADGui as Gui
import FreeCAD as App
from freecad.metalwb import ICONPATH

class MetalWorkbench(Gui.Workbench):

    MenuText = "MetalWB"
    ToolTip = "Design of metalworking parts and assemblies"
    Icon = os.path.join(ICONPATH, "metalwb.svg")

    toolbox_welding = [
        "WarehouseProfiles",
        "MetalWB_Trim",
        "OverlapDetect",
        "MetalWB_Corner"
    ]
    toolbox_drawing = [
        "Sketcher_NewSketch",
        "MyCube",
        "Part_Fuse",
        "Part_Cut",
        "MetalWB_Line",
        "MetalWB_SplitCurves",
        "MetalWB_Discretize"
    ]
    toolbox_design = [
        "PartDesign_Body",
        "PartDesign_Pad",
        "PartDesign_Pocket"
    ]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        from freecad.metalwb import my_cube_tool
        from freecad.metalwb import trim_extend
        from freecad.metalwb import corner_tools
        from freecad.metalwb import warehouse_profiles_tool
        from freecad.metalwb import overlap_detection_tool

        from freecad.metalwb import curves_line_fp
        from freecad.metalwb import curves_discretize
        from freecad.metalwb import curves_split_curves

        import SketcherGui
        import PartDesignGui

        App.Console.PrintMessage("switching to Metal workbench\n")

        self.appendToolbar("Welding", self.toolbox_welding)
        self.appendMenu("Welding", self.toolbox_welding)

        self.appendToolbar("Part Design", self.toolbox_design)
        self.appendMenu("Part Design", self.toolbox_design)

        self.appendToolbar("Drawing", self.toolbox_drawing)
        self.appendMenu("Drawing", self.toolbox_drawing)

    def Activated(self):
        '''
        code which should be computed when a user switch to this workbench
        '''
        # This command will get group of parameters if it exist otherwise it will create a new one
        p = App.ParamGet("User parameter:BaseApp/Preferences/Mod/MetalWB")


        '''
        Theses commands will check if this is the first time the user activated this workbench,
        it will use parameter to check the first_startup status and store the new status
        '''
        is_first_startup = True
        # First check if there is article in group parameters
        if not p.IsEmpty():
            for article in p.GetContents():
                if "first_startup" in article:
                    # first_startup parameter exist so let's get is value
                    is_first_startup = p.GetBool("first_startup")
                else:
                    # If no article then create a boolean one called "first_startup" with True value
                    p.SetBool("first_startup", is_first_startup)
        else:
            # If no article then create a boolean one called "first_startup" with True value
            p.SetBool("first_startup", is_first_startup)
        # now show a QMessageBox if this is the first startup
        if is_first_startup is True:
            App.Console.PrintMessage("Welcome, this is your first time with this workbench\n")
            from PySide import QtGui
            mb = QtGui.QMessageBox()
            mb.setWindowTitle("First time?")
            mb.setText("Do you want to see a tutorial?")
            cb = QtGui.QCheckBox("Don't show this message again")
            mb.setCheckBox(cb)
            mb.setStandardButtons(mb.Yes | mb.No)
            reply = mb.exec_()
            if cb.isChecked():
                p.SetBool("first_startup", False)
            else:
                p.SetBool("first_startup", True)
            if reply == mb.No:
                App.Console.PrintMessage("Ok, no problem\n")
                pass
            elif reply == mb.Yes:
                App.Console.PrintMessage("Ok, let's go!\n")
                pass
        pass

    def Deactivated(self):
        '''
        code which should be computed when this workbench is deactivated
        '''
        pass

    def check_workbench(self, workbench):
        # checks whether the specified workbench (a 'string') is installed
        list_wb = Gui.listWorkbenches()
        has_wb = False
        for wb in list_wb.keys():
            if wb == workbench:
                has_wb = True
        return has_wb

    def dot(self):
        # makes a kind of progress bar
        App.Console.PrintMessage(".")
        Gui.updateGui()

Gui.addWorkbench(MetalWorkbench())
