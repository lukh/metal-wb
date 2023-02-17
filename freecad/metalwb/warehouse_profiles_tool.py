# coding: utf-8
# This function is based on WarehouseProfiles.py macro, by Vincent Ballu (2021)
# Quentin Plisson
# Jonathan Wiedemann
# Mario52

# Import statements
import os
import FreeCAD as App
import Part
import math
from freecad.metalwb import ICONPATH
from freecad.metalwb import RESOURCESPATH
from freecad.metalwb import WAREHOUSEPATH

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

# Global variable for a 3D float vector (used in Profile class)
vec = App.Base.Vector


class Box(QtGui.QDialog):
    """
    Dialog box for WarehouseProfiles, based on PySide.QtGui.QDialog class.
    """

    def __init__(self, lib_path):
        """
        User interface (UI) initialization with a default family, dimensions and parameters of profile.
        List of values are in profiles library file ("Profiles.txt"), founded with 'lib_path' parameter.
        """
        fam_init_index = 8
        dim_init_index = 1
        len_init = 100
        #
        self.lib_path = lib_path
        self.fams_list = listing_families(self.lib_path)
        self.fam = self.fams_list[fam_init_index]
        self.dims_list = listing_family_dimensions(self.lib_path, self.fam)
        self.dim = self.dims_list[dim_init_index]
        # Boolean variable for combo boxes
        self.make_fillet = True
        self.reverse_attachment = False
        self.height_centered = True
        self.width_centered = True
        self.size_name = False
        self.bevels_combined = False
        #
        self.length = len_init
        # Update of dimensions
        self.update_data()
        # Call the parent class with "super"
        super(Box, self).__init__(Gui.getMainWindow(), QtCore.Qt.Tool)
        # Call the UI initialization function
        self.init_user_interface()

    def init_user_interface(self):
        """
        Abbreviation used for widgets:
        - window = win ;
        - label = lbl ;
        - combo box = combo ;
        - spinbox = sb ;
        - checkbox = cb.
        """

        self.setWindowTitle("Profile Warehouse")
        self.setWindowIcon(QtGui.QIcon(os.path.join(ICONPATH, "warehouse_profiles.svg")))

        QtCore.Qt.WA_DeleteOnClose

        """ 'Apply a profile' group box """

        # graphics View
        ####Screen Graphic BitMap
        ##https://doc.qt.io/qtforpython/PySide2/QtCore/Qt.html
        self.graphicsView = QtGui.QGraphicsView()
        self.graphicsView.setFixedSize(320,160)
        self.pic = QtGui.QPixmap()
        self.pic.load(os.path.join(WAREHOUSEPATH,'Warehouse.png'))  #indoor_Icon_b64  # bmp converti
        self.scene = QtGui.QGraphicsScene()
        self.scene.addPixmap(QtGui.QPixmap(self.pic))
        self.graphicsView.setScene(self.scene)
        # graphics View

        # Hbox for graphics View
        hbox_img = QtGui.QHBoxLayout()
        hbox_img.addWidget(self.graphicsView)

        # OK button
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setMinimumHeight(40)
        btn_ok.clicked.connect(self.onclick_ok)

        # Cancel button
        btn_cancel = QtGui.QPushButton("Cancel")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.onclick_cancel)

        # Hbox for command buttons
        hbox_cmd = QtGui.QHBoxLayout()
        hbox_cmd.addWidget(btn_ok)
        hbox_cmd.addWidget(btn_cancel)

        # Families section label
        self.lbl_family = QtGui.QLabel("Family", self)
        new_font = QtGui.QFont(self.lbl_family.font())
        new_font.setPointSize(10)
        self.lbl_family.setFont(new_font)

        # Families section combo box
        self.combo_family = QtGui.QComboBox(self)
        self.combo_family.setToolTip("Choose kind of profile")
        self.combo_family.addItems(self.fams_list)
        self.combo_family.setCurrentIndex(self.fams_list.index(self.fam))
        self.combo_family.activated[str].connect(self.on_combo_family_changed)
        self.combo_family.textHighlighted.connect(self.on_FamilyChange)
        self.on_FamilyChange(self.fam)

        # Hbox for families
        hbox_fam = QtGui.QHBoxLayout()
        hbox_fam.addWidget(self.lbl_family)
        hbox_fam.addWidget(self.combo_family)

        # Size section label
        self.lbl_size = QtGui.QLabel("Size", self)
        new_font = QtGui.QFont(self.lbl_size.font())
        new_font.setPointSize(10)
        self.lbl_size.setFont(new_font)
        # self.lbl_size.move(190, 8)

        # Size section combo box
        self.combo_size = QtGui.QComboBox(self)
        self.combo_size.setToolTip("Choose size")
        self.combo_size.addItems(self.dims_list)
        self.combo_size.setCurrentIndex(self.dims_list.index(self.dim))
        self.combo_size.activated[str].connect(self.on_combo_size_changed)

        # Hbox for size section
        hbox_size = QtGui.QHBoxLayout()
        hbox_size.addWidget(self.lbl_size)
        hbox_size.addWidget(self.combo_size)

        # VBox for apply group
        vbox_apply = QtGui.QVBoxLayout()
        vbox_apply.addLayout(hbox_img)
        vbox_apply.addLayout(hbox_cmd)
        vbox_apply.addLayout(hbox_fam)
        vbox_apply.addLayout(hbox_size)

        # Create 'Apply a profile' group box
        self.group_box_apply = QtGui.QGroupBox("Apply a profile on selected wires :")
        self.group_box_apply.setLayout(vbox_apply)

        """ 'Dimmensions setting' group box """

        # Height - Label
        self.lbl_height = QtGui.QLabel("Height or diameter", self)
        # Height - Spin box
        self.sb_height = QtGui.QDoubleSpinBox(self)
        sb_height = self.sb_height
        sb_height.setToolTip("Adjust height")
        sb_height.setDecimals(1)
        sb_height.setMinimum(0.1)
        sb_height.setMaximum(1000.0)
        sb_height.setSingleStep(0.1)
        sb_height.setProperty("value", self.height)
        sb_height.setObjectName("height")
        # Height - Horizontal layout box
        hbox_height = QtGui.QHBoxLayout()
        hbox_height.addWidget(self.lbl_height)
        hbox_height.addWidget(sb_height)

        # Width - Label
        self.lbl_width = QtGui.QLabel("Width", self)
        # Width - Spin box
        self.sb_width = QtGui.QDoubleSpinBox(self)
        sb_width = self.sb_width
        sb_width.setToolTip("Adjust width")
        sb_width.setDecimals(1)
        sb_width.setMinimum(0.0)
        sb_width.setMaximum(1000.0)
        sb_width.setSingleStep(0.1)
        sb_width.setProperty("value", self.width)
        sb_width.setObjectName("width")
        # Width - Horizontal layout box
        hbox_width = QtGui.QHBoxLayout()
        hbox_width.addWidget(self.lbl_width)
        hbox_width.addWidget(sb_width)

        # Main Thickness - Label
        self.lbl_main_thickness = QtGui.QLabel("Main Thickness", self)
        # Main Thickness - Spin box
        self.sb_main_thickness = QtGui.QDoubleSpinBox(self)
        sb_thickness = self.sb_main_thickness
        sb_thickness.setToolTip("Adjust main or web thickness")
        sb_thickness.setDecimals(2)
        sb_thickness.setMinimum(0)
        sb_thickness.setMaximum(100.0)
        sb_thickness.setSingleStep(0.01)
        sb_thickness.setProperty("value", self.main_thickness)
        sb_thickness.setObjectName("mainthickness")
        # Main Thickness - Horizontal layout box
        hbox_thickness = QtGui.QHBoxLayout()
        hbox_thickness.addWidget(self.lbl_main_thickness)
        hbox_thickness.addWidget(sb_thickness)

        # Flange Thickness - Label
        self.lbl_flange_thickness = QtGui.QLabel("Flange Thickness", self)
        # Flange Thickness - Spin box
        self.sb_flange_thickness = QtGui.QDoubleSpinBox(self)
        sb_flange = self.sb_flange_thickness
        sb_flange.setToolTip("Adjust flange thickness")
        sb_flange.setDecimals(1)
        sb_flange.setMinimum(0)
        sb_flange.setMaximum(100.0)
        sb_flange.setSingleStep(0.1)
        sb_flange.setProperty("value", self.flange_thickness)
        sb_flange.setObjectName("flangethickness")
        # Flange Thickness - Horizontal layout box
        hbox_flange = QtGui.QHBoxLayout()
        hbox_flange.addWidget(self.lbl_flange_thickness)
        hbox_flange.addWidget(sb_flange)

        # Lenght - Label
        self.lbl_length = QtGui.QLabel("Length", self)
        # Lenght - Spin box
        self.sb_length = QtGui.QDoubleSpinBox(self)
        sb_len = self.sb_length
        sb_len.setToolTip("Set length if not attached")
        sb_len.setDecimals(1)
        sb_len.setMinimum(0)
        sb_len.setMaximum(24000.0)
        sb_len.setSingleStep(1)
        sb_len.setProperty("value", self.length)
        sb_len.setObjectName("length")
        # Lenght - Horizontal layout box
        hbox_len = QtGui.QHBoxLayout()
        hbox_len.addWidget(self.lbl_length)
        hbox_len.addWidget(sb_len)

        # Large Radius - Label
        self.lbl_radius1 = QtGui.QLabel("Large radius", self)
        # Large Radius - Spin box
        self.sb_radius1 = QtGui.QDoubleSpinBox(self)
        sb_r1 = self.sb_radius1
        sb_r1.setToolTip("Adjust Radius 1")
        sb_r1.setDecimals(1)
        sb_r1.setMinimum(0)
        sb_r1.setMaximum(50)
        sb_r1.setSingleStep(0.1)
        sb_r1.setProperty("value", self.radius1)
        sb_r1.setObjectName("radius1")
        # Large Radius - Horizontal layout box
        hbox_r1 = QtGui.QHBoxLayout()
        hbox_r1.addWidget(self.lbl_radius1)
        hbox_r1.addWidget(sb_r1)

        # Small Radius - Label
        self.lbl_radius2 = QtGui.QLabel("Small radius", self)
        # Small Radius - Spin box
        self.sb_radius2 = QtGui.QDoubleSpinBox(self)
        sb_r2 = self.sb_radius2
        sb_r2.setToolTip("Adjust Radius 2")
        sb_r2.setDecimals(1)
        sb_r2.setMinimum(0)
        sb_r2.setMaximum(50)
        sb_r2.setSingleStep(0.1)
        sb_r2.setProperty("value", self.radius2)
        sb_r2.setObjectName("radius2")
        # Small Radius - Horizontal layout box
        hbox_r2 = QtGui.QHBoxLayout()
        hbox_r2.addWidget(self.lbl_radius2)
        hbox_r2.addWidget(sb_r2)

        # 'Dimmensions settings' group box vertical layout
        vbox_dim = QtGui.QVBoxLayout()
        vbox_dim.addLayout(hbox_height)
        vbox_dim.addLayout(hbox_width)
        vbox_dim.addLayout(hbox_len)
        vbox_dim.addLayout(hbox_thickness)
        vbox_dim.addLayout(hbox_flange)
        vbox_dim.addLayout(hbox_r1)
        vbox_dim.addLayout(hbox_r2)

        # 'Dimmensions settings' group box creation
        self.group_box_dim = QtGui.QGroupBox("Dimmensions settings")
        self.group_box_dim.setLayout(vbox_dim)

        """ Checkboxes group box """

        # Checkbox 1 / Fillet or not
        self.cb_make_fillet = QtGui.QCheckBox("Make Fillets", self)
        cb1 = self.cb_make_fillet
        cb1.setChecked(True)
        cb1.clicked.connect(self.on_checkbox1_active)

        # Checkbox 2 / Reverse attachment
        self.cb_reverse_attachment = QtGui.QCheckBox("Reverse Attachment", self)
        cb2 = self.cb_reverse_attachment
        cb2.clicked.connect(self.on_checkbox2_active)

        # Checkbox 3 / Height centered
        self.cb_height_centered = QtGui.QCheckBox("Height Centered", self)
        cb3 = self.cb_height_centered
        cb3.setChecked(True)
        cb3.clicked.connect(self.on_checkbox3_active)

        # Checkbox 4 / Widht centered
        self.cb_width_centered = QtGui.QCheckBox("Width Centered", self)
        cb4 = self.cb_width_centered
        cb4.setChecked(True)
        cb4.clicked.connect(self.on_checkbox4_active)

        # Checkbox 5 / Size in object name
        self.size_in_name = QtGui.QCheckBox("Size in object name", self)
        cb5 = self.size_in_name
        cb5.setChecked(True)
        cb5.clicked.connect(self.on_checkbox5_active)

        # Checkbox 6 / Combined bevel
        self.combined_bevel = QtGui.QCheckBox("Combined Bevels", self)
        cb6 = self.combined_bevel
        cb6.clicked.connect(self.on_checkbox6_active)

        # Layout
        hbox_12 = QtGui.QHBoxLayout()
        hbox_12.addWidget(cb1)
        hbox_12.addWidget(cb2)
        hbox_34 = QtGui.QHBoxLayout()
        hbox_34.addWidget(cb3)
        hbox_34.addWidget(cb4)
        hbox_56 = QtGui.QHBoxLayout()
        hbox_56.addWidget(cb5)
        hbox_56.addWidget(cb6)

        vbox_check = QtGui.QVBoxLayout()
        vbox_check.addLayout(hbox_12)
        vbox_check.addLayout(hbox_34)
        vbox_check.addLayout(hbox_56)

        self.group_box_check = QtGui.QGroupBox("Checkboxes")
        self.group_box_check.setLayout(vbox_check)

        """ Attachment group box """

        # Attachment - Label
        self.lbl_attach = QtGui.QLabel("", self)
        new_font = QtGui.QFont(self.lbl_attach.font())
        new_font.setPointSize(10)
        self.lbl_attach.setFont(new_font)
        self.update_selection("", "")

        # VBox
        vbox_attach = QtGui.QVBoxLayout()
        vbox_attach.addWidget(self.lbl_attach)

        # 'Attachment' group box creation
        self.group_box_attach = QtGui.QGroupBox("Attachment")
        self.group_box_attach.setLayout(vbox_attach)

        """ Vertical layout """

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.group_box_apply)
        vbox.addWidget(self.group_box_dim)
        vbox.addWidget(self.group_box_check)
        vbox.addWidget(self.group_box_attach)

        self.setLayout(vbox)

    def onclick_cancel(self):
        self.close()

    def onclick_ok(self):
        """
        Generate one or more profiles according to selected edges.
        """
        # Transaction
        App.ActiveDocument.openTransaction("Add Profile")
        selection_list = Gui.Selection.getSelectionEx()
        for selected_obj in selection_list:
            indent = 0
            sub_list = selected_obj.SubObjects
            for i in sub_list:
                self.makeProfile(selected_obj, sub_list, indent)
                indent += 1
        App.ActiveDocument.commitTransaction()
        

    def makeProfile(self, selected_obj, sub_list, indent):
        selected_sub = sub_list[indent]
        selected_sub_name = selected_obj.SubElementNames[indent]
        print("Selected sub-object " + str(indent+1) + " : " + selected_sub_name)
        # Definition of profile object name
        if self.size_in_name:
            obj_name = self.fam + "_" + self.dim + "_"
        else:
            obj_name = self.fam
        # Create an object in current document
        obj = App.ActiveDocument.addObject("Part::FeaturePython", obj_name)
        obj.addExtension("Part::AttachExtensionPython")
        # Create a ViewObject in current GUI
        obj.ViewObject.Proxy = 0
        view_obj = Gui.ActiveDocument.getObject(obj.Name)
        view_obj.DisplayMode = "Flat Lines"
        link_sub = ""
        # "try" block generates an exception if no block is selected ("except" blocks below)
        try:
            # Tuple assignment for edge
            feature = selected_obj.Object
            link_sub = (feature, (selected_obj.SubElementNames[indent]))
            edge_name = selected_obj.SubElementNames[indent]
            lg = selected_sub.Length
            obj.MapMode = "NormalToEdge"
            obj.Support = (feature, edge_name)
            #
            if not self.reverse_attachment:
                #print("Not reverse attachment")
                obj.MapPathParameter = 1
            else:
                #print("Reverse attachment")
                obj.MapPathParameter = 0
                obj.MapReversed = True
            #
            indent = indent + 1
        # Exceptions
        except NameError:
            print("A variable is not defined.")
        except AttributeError:
            print("Error on the attribute assignment or reference fails.")
        except ValueError:
            print("A function gets an argument of correct type but improper value.")
        except IndentationError:
            print("There is an incorrect indentation.")
        except:
            print("Unidentified error.")

        # Abbreviation of parameters to call Profile class
        wd = self.sb_width.value()
        ht = self.sb_height.value()
        mt = self.sb_main_thickness.value()
        ft = self.sb_flange_thickness.value()
        r1 = self.sb_radius1.value()
        r2 = self.sb_radius2.value()
        if link_sub == "": lg = self.sb_length.value()
        wt = float(self.weight)
        if self.fam == "Flat Sections" or self.fam == "Square": self.make_fillet = False
        mf = self.make_fillet
        hc = self.height_centered
        wc = self.width_centered
        bc = self.bevels_combined

        Profile(obj, link_sub, wd, ht, mt, ft, r1, r2, lg, wt, mf, hc, wc, self.fam, bc)

        # Recompute working document :
        try:
            # the one which contain selection,
            dm = selection_list.Document
        except:
            # or the one which is active
            dm = App.activeDocument()
        dm.recompute()

    def on_checkbox1_active(self, state):
        self.make_fillet = state
        self.on_FamilyChange(self.combo_family.currentText())

    def on_checkbox2_active(self, state):
        self.reverse_attachment = state

    def on_checkbox3_active(self, state):
        self.height_centered = state

    def on_checkbox4_active(self, state):
        self.width_centered = state

    def on_checkbox5_active(self, state):
        self.size_in_name = state

    def on_checkbox6_active(self, state):
        self.bevels_combined = state

    def on_FamilyChange(self, txt):       # display the image in window 

        if self.make_fillet:
            if txt == "Equal Leg Angles":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Equal_Leg_Angles_Fillet.png'))#
            elif txt == "Unequal Leg Angles":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Unequal_Leg_Angles_Fillet.png'))#
            elif txt == "Flat Sections":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Flat_Sections.png'))
            elif txt == "Square":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Square_Fillet.png'))
            elif txt == "Square Hollow":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Square_Hollow_Fillet.png'))
            elif txt == "Rectangular Hollow":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Rectangular_Hollow_Fillet.png'))
            elif txt == "UPE":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'UPE_Fillet.png'))
            elif txt == "UPN":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'UPN_Fillet.png'))
            elif txt == "HEA":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEA_Fillet.png'))
            elif txt == "HEB":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEB_Fillet.png'))
            elif txt == "HEM":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEM_Fillet.png'))
            elif txt == "IPE":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'IPE_Fillet.png'))
            elif txt == "IPN":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'IPN_Fillet.png'))
            elif txt == "Round bar":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Round_Bar.png'))
            elif txt == "Pipe":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Pipe.png'))
            else:
                self.pic.load(os.path.join(WAREHOUSEPATH, 'WareHouse.png'))
        else:
            if txt == "Equal Leg Angles":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Equal_Leg_Angles.png'))#
            elif txt == "Unequal Leg Angles":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Unequal_Leg_Angles.png'))#
            elif txt == "Flat Sections":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Flat_Sections.png'))
            elif txt == "Square":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Square.png'))
            elif txt == "Square Hollow":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Square_Hollow.png'))
            elif txt == "Rectangular Hollow":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Rectangular_Hollow.png'))
            elif txt == "UPE":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'UPE.png'))
            elif txt == "UPN":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'UPN.png'))
            elif txt == "HEA":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEA.png'))
            elif txt == "HEB":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEB.png'))
            elif txt == "HEM":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'HEM.png'))
            elif txt == "IPE":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'IPE.png'))
            elif txt == "IPN":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'IPN.png'))
            elif txt == "Round bar":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Round_Bar.png'))
            elif txt == "Pipe":
                self.pic.load(os.path.join(WAREHOUSEPATH, 'Pipe.png'))
            else:
                self.pic.load(os.path.join(WAREHOUSEPATH, 'WareHouse.png'))

        self.scene.addPixmap(QtGui.QPixmap(self.pic))
        self.graphicsView.setScene(self.scene)

    

    def on_combo_family_changed(self, txt):
        self.on_FamilyChange( txt)
        self.fam = txt
        self.dims_list = listing_family_dimensions(self.lib_path, self.fam)
        self.dim = self.dims_list[0]
        self.combo_size.clear()
        self.combo_size.addItems(self.dims_list)
        self.combo_size.setCurrentIndex(self.dims_list.index(self.dim))
        self.update_data()
        self.update_box()

    def on_combo_size_changed(self, txt):
        self.dim = txt
        self.update_data()
        self.update_box()

    def update_data(self):
        """
        Associates each dimension of a profile with its value, contained in the "data" list
        """
        self.data = extract_data(self.lib_path, self.fam, self.dim)

        try:
            height_index = search_index(self.lib_path, self.fam, "Height")
            self.height = self.data[height_index]
        except:
            self.height = 0
        try:
            width_index = search_index(self.lib_path, self.fam, "Width")
            self.width = self.data[width_index]
        except:
            self.width = 0
        try:
            main_thickness_index = search_index(self.lib_path, self.fam, "Thickness")
            self.main_thickness = self.data[main_thickness_index]
        except:
            self.main_thickness = 0
        try:
            flange_thickness_index = search_index(self.lib_path, self.fam, "Flange Thickness")
            self.flange_thickness = self.data[flange_thickness_index]
        except:
            self.flange_thickness = 0
        try:
            radius1_index = search_index(self.lib_path, self.fam, "Radius1")
            self.radius1 = self.data[radius1_index]
        except:
            self.radius1 = 0
        try:
            radius2_index = search_index(self.lib_path, self.fam, "Radius2")
            self.radius2 = self.data[radius2_index]
        except:
            self.radius2 = 0
        try:
            weight_index = search_index(self.lib_path, self.fam, "Weight")
            self.weight = self.data[weight_index]
        except:
            self.weight = 0

    def update_box(self):
        """

        """
        self.sb_height.setProperty("value", self.height)
        self.sb_width.setProperty("value", self.width)
        self.sb_main_thickness.setProperty("value", self.main_thickness)
        self.sb_flange_thickness.setProperty("value", self.flange_thickness)
        self.sb_length.setProperty("value", self.length)
        self.sb_radius1.setProperty("value", self.radius1)
        self.sb_radius2.setProperty("value", self.radius2)

    def update_selection(self, new_obj, new_sub):
        """
        objet sélectionné -> 1 de la liste
        edge -> sous-élément de l'objet
        """
        obj_name = ''
        try:  # first run

            for sel in Gui.Selection.getSelectionEx():
                selected_obj_name = sel.ObjectName
                subs = ''
                for sub in sel.SubElementNames:
                    subs += '{},'.format(sub)

                obj_name += selected_obj_name 
                obj_name += " / "
                obj_name += subs
                obj_name += '\n'
        except:
            obj_name = "Attachment: None"

        self.lbl_attach.setText(obj_name)
        #print("Updated attachment :", obj_name)


class SelObserver:
    """
    SelectionObserver class simplifies the step to write classes that listen to what happens to the selection?
    """

    def __init__(self, form):
        self.form = form

    def addSelection(self, doc, obj, sub, other):
        self.form.update_selection(obj, sub)

    def clearSelection(self, other):
        self.form.update_selection("", "")


class Profile:
    """
    Profile(obj, link_sub, wd, ht, mt, ft, r1, r2, lg, wt, self.mf, hc, wc, self.fam, bc)
    """

    def __init__(self, obj, link_sub, init_w, init_h, init_mt, init_ft, init_r1, init_r2, init_len, init_wg, init_mf,
                 init_hc, init_wc, fam, bevels_combined):
        """
        Constructor. Add properties to FreeCAD Profile object. Profile object have 11 nominal properties associated
        with initialization value 'init_w' to 'init_wc' : ProfileHeight, ProfileWidth, [...] CenteredOnWidth. Depending
        on 'bevels_combined' parameters, there is 4 others properties for bevels : BevelStartCut1, etc. Depending on
        'fam' parameter, there is properties specific to profile family.
        """

        obj.addProperty("App::PropertyFloat", "ProfileHeight", "Profile", "", ).ProfileHeight = init_h
        obj.addProperty("App::PropertyFloat", "ProfileWidth", "Profile", "").ProfileWidth = init_w
        obj.addProperty("App::PropertyFloat", "ProfileLength", "Profile", "").ProfileLength = init_len

        obj.addProperty("App::PropertyFloat", "Thickness", "Profile",
                        "Thickness of all the profile or the web").Thickness = init_mt
        obj.addProperty("App::PropertyFloat", "ThicknessFlange", "Profile",
                        "Thickness of the flanges").ThicknessFlange = init_ft

        obj.addProperty("App::PropertyFloat", "RadiusLarge", "Profile", "Large radius").RadiusLarge = init_r1
        obj.addProperty("App::PropertyFloat", "RadiusSmall", "Profile", "Small radius").RadiusSmall = init_r2
        obj.addProperty("App::PropertyBool", "MakeFillet", "Profile",
                        "Wheter to draw the fillets or not").MakeFillet = init_mf

        if not bevels_combined:
            obj.addProperty("App::PropertyFloat", "BevelStartCut1", "Profile",
                            "Bevel on First axle at the start of the profile").BevelStartCut1 = 0
            obj.addProperty("App::PropertyFloat", "BevelStartCut2", "Profile",
                            "Rotate the cut on Second axle at the start of the profile").BevelStartCut2 = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut1", "Profile",
                            "Bevel on First axle at the end of the profile").BevelEndCut1 = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut2", "Profile",
                            "Rotate the cut on Second axle at the end of the profile").BevelEndCut2 = 0
        if bevels_combined:
            obj.addProperty("App::PropertyFloat", "BevelStartCut", "Profile",
                            "Bevel at the start of the profile").BevelStartCut = 0
            obj.addProperty("App::PropertyFloat", "BevelStartRotate", "Profile",
                            "Rotate the second cut on Profile axle").BevelStartRotate = 0
            obj.addProperty("App::PropertyFloat", "BevelEndCut", "Profile",
                            "Bevel on First axle at the end of the profile").BevelEndCut = 0
            obj.addProperty("App::PropertyFloat", "BevelEndRotate", "Profile",
                            "Rotate the second cut on Profile axle").BevelEndRotate = 0

        obj.addProperty("App::PropertyFloat", "ApproxWeight", "Base",
                        "Approximate weight in Kilogram").ApproxWeight = init_wg * init_len / 1000

        obj.addProperty("App::PropertyBool", "CenteredOnHeight", "Profile",
                        "Choose corner or profile centre as origin").CenteredOnHeight = init_hc
        obj.addProperty("App::PropertyBool", "CenteredOnWidth", "Profile",
                        "Choose corner or profile centre as origin").CenteredOnWidth = init_wc

        if fam == "UPE":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57
        if fam == "UPN":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57

        if fam == "IPE" or fam == "HEA" or fam == "HEB" or fam == "HEM":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8
        if fam == "IPN":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8

        obj.addProperty("App::PropertyLength", "Width", "Structure",
                        "Parameter for structure").Width = obj.ProfileWidth  # Property for structure
        obj.addProperty("App::PropertyLength", "Height", "Structure",
                        "Parameter for structure").Height = obj.ProfileLength  # Property for structure
        obj.addProperty("App::PropertyLength", "Length", "Structure",
                        "Parameter for structure", ).Length = obj.ProfileHeight  # Property for structure
        obj.setEditorMode("Width", 1)  # user doesn't change !
        obj.setEditorMode("Height", 1)
        obj.setEditorMode("Length", 1)

        obj.addProperty("App::PropertyFloat", "OffsetA", "Structure",
                        "Parameter for structure").OffsetA = .0  # Property for structure

        obj.addProperty("App::PropertyFloat", "OffsetB", "Structure",
                        "Parameter for structure").OffsetB = .0  # Property for structure

        if link_sub:
            obj.addProperty("App::PropertyLinkSub", "Target", "Base", "Target face").Target = link_sub
            obj.setExpression('.AttachmentOffset.Base.z', u'-OffsetA')

        self.WM = init_wg
        self.fam = fam
        self.bevels_combined = bevels_combined
        obj.Proxy = self

    def on_changed(self, obj, p):

        if p == "ProfileWidth" or p == "ProfileHeight" or p == "Thickness" \
                or p == "FilletRadius" or p == "Centered" or p == "Length" \
                or p == "BevelStartCut1" or p == "BevelEndCut1" \
                or p == "BevelStartCut2" or p == "BevelEndCut2" \
                or p == "BevelStartCut" or p == "BevelEndCut" \
                or p == "BevelStartRotate" or p == "BevelEndRotate" \
                or p == "OffsetA" or p == "OffsetB" :
            self.execute(obj)

    def execute(self, obj):

        try:
            L = obj.Target[0].getSubObject(obj.Target[1][0]).Length
            L += obj.OffsetA + obj.OffsetB
            obj.ProfileLength = L
        except:
            L = obj.ProfileLength + obj.OffsetA + obj.OffsetB

        obj.ApproxWeight = self.WM * L / 1000
        W = obj.ProfileWidth
        H = obj.ProfileHeight
        obj.Height = L
        pl = obj.Placement
        TW = obj.Thickness
        TF = obj.ThicknessFlange

        R = obj.RadiusLarge
        r = obj.RadiusSmall
        d = vec(0, 0, 1)

        if W == 0: W = H
        w = h = 0

        if self.bevels_combined == False:
            if obj.BevelStartCut1 > 60: obj.BevelStartCut1 = 60
            if obj.BevelStartCut1 < -60: obj.BevelStartCut1 = -60
            if obj.BevelStartCut2 > 60: obj.BevelStartCut2 = 60
            if obj.BevelStartCut2 < -60: obj.BevelStartCut2 = -60

            if obj.BevelEndCut1 > 60: obj.BevelEndCut1 = 60
            if obj.BevelEndCut1 < -60: obj.BevelEndCut1 = -60
            if obj.BevelEndCut2 > 60: obj.BevelEndCut2 = 60
            if obj.BevelEndCut2 < -60: obj.BevelEndCut2 = -60

            B1Y = obj.BevelStartCut1
            B2Y = -obj.BevelEndCut1
            B1X = -obj.BevelStartCut2
            B2X = obj.BevelEndCut2
            B1Z = 0
            B2Z = 0

        if self.bevels_combined == True:
            if obj.BevelStartCut > 60: obj.BevelStartCut = 60
            if obj.BevelStartCut < -60: obj.BevelStartCut = -60
            if obj.BevelStartRotate > 60: obj.BevelStartRotate = 60
            if obj.BevelStartRotate < -60: obj.BevelStartRotate = -60

            if obj.BevelEndCut > 60: obj.BevelEndCut = 60
            if obj.BevelEndCut < -60: obj.BevelEndCut = -60
            if obj.BevelEndRotate > 60: obj.BevelEndRotate = 60
            if obj.BevelEndRotate < -60: obj.BevelEndRotate = -60

            B1Y = obj.BevelStartCut
            B1Z = -obj.BevelStartRotate
            B2Y = -obj.BevelEndCut
            B2Z = -obj.BevelEndRotate
            B1X = 0
            B2X = 0

        if obj.CenteredOnWidth == True:  w = -W / 2
        if obj.CenteredOnHeight == True: h = -H / 2

        if self.fam == "Equal Leg Angles" or self.fam == "Unequal Leg Angles":
            if obj.MakeFillet == False:
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(TW + w, H + h, 0)
                p4 = vec(TW + w, TW + h, 0)
                p5 = vec(W + w, TW + h, 0)
                p6 = vec(W + w, 0 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6])

            if obj.MakeFillet == True:
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(TW - r + w, H + h, 0)
                p4 = vec(TW + w, H - r + h, 0)
                p5 = vec(TW + w, TW + R + h, 0)
                p6 = vec(TW + R + w, TW + h, 0)
                p7 = vec(W - r + w, TW + h, 0)
                p8 = vec(W + w, TW - r + h, 0)
                p9 = vec(W + w, 0 + h, 0)
                c1 = vec(TW - r + w, H - r + h, 0)
                c2 = vec(TW + R + w, TW + R + h, 0)
                c3 = vec(W - r + w, TW - r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p8, p9)
                L6 = Part.makeLine(p9, p1)
                A1 = Part.makeCircle(r, c1, d, 0, 90)
                A2 = Part.makeCircle(R, c2, d, 180, 270)
                A3 = Part.makeCircle(r, c3, d, 0, 90)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, A3, L5, L6])

            p = Part.Face(wire1)

        if self.fam == "Flat Sections" or self.fam == "Square" or self.fam == "Square Hollow" or self.fam == "Rectangular Hollow":
            wire1 = wire2 = 0

            if self.fam == "Square" or self.fam == "Flat Sections":
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(W + w, H + h, 0)
                p4 = vec(W + w, 0 + h, 0)
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                wire1 = Part.Wire([L1, L2, L3, L4])

            if obj.MakeFillet == False and (self.fam == "Square Hollow" or self.fam == "Rectangular Hollow"):
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(W + w, H + h, 0)
                p4 = vec(W + w, 0 + h, 0)
                p5 = vec(TW + w, TW + h, 0)
                p6 = vec(TW + w, H + h - TW, 0)
                p7 = vec(W + w - TW, H + h - TW, 0)
                p8 = vec(W + w - TW, TW + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p5)

                wire1 = Part.Wire([L1, L2, L3, L4])
                wire2 = Part.Wire([L5, L6, L7, L8])

            if obj.MakeFillet == True and (self.fam == "Square Hollow" or self.fam == "Rectangular Hollow"):
                p1 = vec(0 + w, 0 + R + h, 0)
                p2 = vec(0 + w, H - R + h, 0)
                p3 = vec(R + w, H + h, 0)
                p4 = vec(W - R + w, H + h, 0)
                p5 = vec(W + w, H - R + h, 0)
                p6 = vec(W + w, R + h, 0)
                p7 = vec(W - R + w, 0 + h, 0)
                p8 = vec(R + w, 0 + h, 0)

                c1 = vec(R + w, R + h, 0)
                c2 = vec(R + w, H - R + h, 0)
                c3 = vec(W - R + w, H - R + h, 0)
                c4 = vec(W - R + w, R + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(R, c1, d, 180, 270)
                A2 = Part.makeCircle(R, c2, d, 90, 180)
                A3 = Part.makeCircle(R, c3, d, 0, 90)
                A4 = Part.makeCircle(R, c4, d, 270, 0)

                wire1 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

                p1 = vec(TW + w, TW + r + h, 0)
                p2 = vec(TW + w, H - TW - r + h, 0)
                p3 = vec(TW + r + w, H - TW + h, 0)
                p4 = vec(W - TW - r + w, H - TW + h, 0)
                p5 = vec(W - TW + w, H - TW - r + h, 0)
                p6 = vec(W - TW + w, TW + r + h, 0)
                p7 = vec(W - TW - r + w, TW + h, 0)
                p8 = vec(TW + r + w, TW + h, 0)

                c1 = vec(TW + r + w, TW + r + h, 0)
                c2 = vec(TW + r + w, H - TW - r + h, 0)
                c3 = vec(W - TW - r + w, H - TW - r + h, 0)
                c4 = vec(W - TW - r + w, TW + r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(r, c1, d, 180, 270)
                A2 = Part.makeCircle(r, c2, d, 90, 180)
                A3 = Part.makeCircle(r, c3, d, 0, 90)
                A4 = Part.makeCircle(r, c4, d, 270, 0)

                wire2 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

            if wire2:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)

        if self.fam == "UPE" or self.fam == "UPN":
            if obj.MakeFillet == False:  # UPE ou UPN sans arrondis

                Yd = 0
                if obj.UPN == True: Yd = (W / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(w, h, 0)
                p2 = vec(w, H + h, 0)
                p3 = vec(w + W, H + h, 0)
                p4 = vec(W + w, h, 0)
                p5 = vec(W + w + Yd - TW, h, 0)
                p6 = vec(W + w - Yd - TW, H + h - TF, 0)
                p7 = vec(w + TW + Yd, H + h - TF, 0)
                p8 = vec(w + TW - Yd, h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8])

            if obj.MakeFillet == True and obj.UPN == False:  # UPE avec arrondis

                p1 = vec(w, h, 0)
                p2 = vec(w, H + h, 0)
                p3 = vec(w + W, H + h, 0)
                p4 = vec(W + w, h, 0)
                p5 = vec(W + w - TW + r, h, 0)
                p6 = vec(W + w - TW, h + r, 0)
                p7 = vec(W + w - TW, H + h - TF - R, 0)
                p8 = vec(W + w - TW - R, H + h - TF, 0)
                p9 = vec(w + TW + R, H + h - TF, 0)
                p10 = vec(w + TW, H + h - TF - R, 0)
                p11 = vec(w + TW, h + r, 0)
                p12 = vec(w + TW - r, h, 0)

                C1 = vec(w + TW - r, h + r, 0)
                C2 = vec(w + TW + R, H + h - TF - R, 0)
                C3 = vec(W + w - TW - R, H + h - TF - R, 0)
                C4 = vec(W + w - TW + r, r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)

                A1 = Part.makeCircle(r, C1, d, 270, 0)
                A2 = Part.makeCircle(R, C2, d, 90, 180)
                A3 = Part.makeCircle(R, C3, d, 0, 90)
                A4 = Part.makeCircle(r, C4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])

            if obj.MakeFillet == True and obj.UPN == True:  # UPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)

                cot1 = r * sina
                y11 = r - cot1
                cot2 = (H / 2 - r) * tana
                cot3 = cot1 * tana
                x11 = TW - cot2 - cot3
                xc1 = TW - cot2 - cot3 - r * cosa
                yc1 = r
                cot8 = (H / 2 - R - TF + R * sina) * tana
                x10 = TW + cot8
                y10 = H - TF - R + R * sina
                xc2 = cot8 + R * cosa + TW
                yc2 = H - TF - R
                x12 = TW - cot2 - cot3 - r * cosa
                y12 = 0
                x9 = cot8 + R * cosa + TW
                y9 = H - TF
                xc3 = W - xc2
                yc3 = yc2
                xc4 = W - xc1
                yc4 = yc1
                x1 = 0
                y1 = 0
                x2 = 0
                y2 = H
                x3 = W
                y3 = H
                x4 = W
                y4 = 0
                x5 = W - x12
                y5 = 0
                x6 = W - x11
                y6 = y11
                x7 = W - x10
                y7 = y10
                x8 = W - x9
                y8 = y9

                c1 = vec(xc1 + w, yc1 + h, 0)
                c2 = vec(xc2 + w, yc2 + h, 0)
                c3 = vec(xc3 + w, yc3 + h, 0)
                c4 = vec(xc4 + w, yc4 + h, 0)

                p1 = vec(x1 + w, y1 + h, 0)
                p2 = vec(x2 + w, y2 + h, 0)
                p3 = vec(x3 + w, y3 + h, 0)
                p4 = vec(x4 + w, y4 + h, 0)
                p5 = vec(x5 + w, y5 + h, 0)
                p6 = vec(x6 + w, y6 + h, 0)
                p7 = vec(x7 + w, y7 + h, 0)
                p8 = vec(x8 + w, y8 + h, 0)
                p9 = vec(x9 + w, y9 + h, 0)
                p10 = vec(x10 + w, y10 + h, 0)
                p11 = vec(x11 + w, y11 + h, 0)
                p12 = vec(x12 + w, y12 + h, 0)

                A1 = Part.makeCircle(r, c1, d, 270, 0 - angarc)
                A2 = Part.makeCircle(R, c2, d, 90, 180 - angarc)
                A3 = Part.makeCircle(R, c3, d, 0 + angarc, 90)
                A4 = Part.makeCircle(r, c4, d, 180 + angarc, 270)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])

            p = Part.Face(wire1)

        if self.fam == "IPE" or self.fam == "IPN" or self.fam == "HEA" or self.fam == "HEB" or self.fam == "HEM":
            XA1 = W / 2 - TW / 2  # face gauche du web
            XA2 = W / 2 + TW / 2  # face droite du web
            if obj.MakeFillet == False:  # IPE ou IPN sans arrondis
                Yd = 0
                if obj.IPN == True: Yd = (W / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, TF + h - Yd, 0)
                p3 = vec(XA1 + w, TF + h + Yd, 0)
                p4 = vec(XA1 + w, H - TF + h - Yd, 0)
                p5 = vec(0 + w, H - TF + h + Yd, 0)
                p6 = vec(0 + w, H + h, 0)
                p7 = vec(W + w, H + h, 0)
                p8 = vec(W + w, H - TF + h + Yd, 0)
                p9 = vec(XA2 + w, H - TF + h - Yd, 0)
                p10 = vec(XA2 + w, TF + h + Yd, 0)
                p11 = vec(W + w, TF + h - Yd, 0)
                p12 = vec(W + w, 0 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p9)
                L9 = Part.makeLine(p9, p10)
                L10 = Part.makeLine(p10, p11)
                L11 = Part.makeLine(p11, p12)
                L12 = Part.makeLine(p12, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == False:  # IPE avec arrondis
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, TF + h, 0)
                p3 = vec(XA1 - R + w, TF + h, 0)
                p4 = vec(XA1 + w, TF + R + h, 0)
                p5 = vec(XA1 + w, H - TF - R + h, 0)
                p6 = vec(XA1 - R + w, H - TF + h, 0)
                p7 = vec(0 + w, H - TF + h, 0)
                p8 = vec(0 + w, H + h, 0)
                p9 = vec(W + w, H + h, 0)
                p10 = vec(W + w, H - TF + h, 0)
                p11 = vec(XA2 + R + w, H - TF + h, 0)
                p12 = vec(XA2 + w, H - TF - R + h, 0)
                p13 = vec(XA2 + w, TF + R + h, 0)
                p14 = vec(XA2 + R + w, TF + h, 0)
                p15 = vec(W + w, TF + h, 0)
                p16 = vec(W + w, 0 + h, 0)

                c1 = vec(XA1 - R + w, TF + R + h, 0)
                c2 = vec(XA1 - R + w, H - TF - R + h, 0)
                c3 = vec(XA2 + R + w, H - TF - R + h, 0)
                c4 = vec(XA2 + R + w, TF + R + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p7, p8)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p9, p10)
                L8 = Part.makeLine(p10, p11)
                L9 = Part.makeLine(p12, p13)
                L10 = Part.makeLine(p14, p15)
                L11 = Part.makeLine(p15, p16)
                L12 = Part.makeLine(p16, p1)

                A1 = Part.makeCircle(R, c1, d, 270, 0)
                A2 = Part.makeCircle(R, c2, d, 0, 90)
                A3 = Part.makeCircle(R, c3, d, 90, 180)
                A4 = Part.makeCircle(R, c4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, L5, L6, L7, L8, A3, L9, A4, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == True:  # IPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)
                cot1 = W / 4 * tana  # 1,47
                cot2 = TF - cot1  # 4,42
                cot3 = r * cosa  # 1,98
                cot4 = r - cot3 * tana  # 1,72
                cot5 = cot4 * tana  # 0,24
                cot5 = cot2 + cot5  # 4,66
                cot6 = R * sina  # 0,55
                cot7 = W / 4 - R - TW / 2  # 4,6
                cot8 = cot6 + cot7  # 5,15
                cot9 = cot7 * tana  # 0,72
                cot10 = R * cosa  # 3,96

                xc1 = r
                yc1 = cot5 - cot3
                c1 = vec(xc1 + w, yc1 + h, 0)

                xc2 = W / 2 - TW / 2 - R
                yc2 = cot9 + TF + cot10
                c2 = vec(xc2 + w, yc2 + h, 0)

                xc3 = xc2
                yc3 = H - yc2
                c3 = vec(xc3 + w, yc3 + h, 0)

                xc4 = xc1
                yc4 = H - yc1
                c4 = vec(xc4 + w, yc4 + h, 0)

                xc5 = W - xc1
                yc5 = yc4
                c5 = vec(xc5 + w, yc5 + h, 0)

                xc6 = W - xc2
                yc6 = yc3
                c6 = vec(xc6 + w, yc6 + h, 0)

                xc7 = xc6
                yc7 = yc2
                c7 = vec(xc7 + w, yc7 + h, 0)

                xc8 = xc5
                yc8 = yc1
                c8 = vec(xc8 + w, yc8 + h, 0)

                A1 = Part.makeCircle(r, c1, d, 90 + angarc, 180)
                A2 = Part.makeCircle(R, c2, d, 270 + angarc, 0)
                A3 = Part.makeCircle(R, c3, d, 0, 90 - angarc)
                A4 = Part.makeCircle(r, c4, d, 180, 270 - angarc)
                A5 = Part.makeCircle(r, c5, d, 270 + angarc, 0)
                A6 = Part.makeCircle(R, c6, d, 90 + angarc, 180)
                A7 = Part.makeCircle(R, c7, d, 180, 270 - angarc)
                A8 = Part.makeCircle(r, c8, d, 0, 90 - angarc)

                xp1 = 0
                yp1 = 0
                p1 = vec(xp1 + w, yp1 + h, 0)

                xp2 = 0
                yp2 = cot5 - cot3
                p2 = vec(xp2 + w, yp2 + h, 0)

                xp3 = cot4
                yp3 = cot5
                p3 = vec(xp3 + w, yp3 + h, 0)

                xp4 = W / 4 + cot8
                yp4 = TF + cot9
                p4 = vec(xp4 + w, yp4 + h, 0)

                xp5 = W / 2 - TW / 2
                yp5 = yc2
                p5 = vec(xp5 + w, yp5 + h, 0)

                xp6 = xp5
                yp6 = H - yp5
                p6 = vec(xp6 + w, yp6 + h, 0)

                xp7 = xp4
                yp7 = H - yp4
                p7 = vec(xp7 + w, yp7 + h, 0)

                xp8 = xp3
                yp8 = H - yp3
                p8 = vec(xp8 + w, yp8 + h, 0)

                xp9 = xp2
                yp9 = H - yp2
                p9 = vec(xp9 + w, yp9 + h, 0)

                xp10 = xp1
                yp10 = H
                p10 = vec(xp10 + w, yp10 + h, 0)

                xp11 = W
                yp11 = H
                p11 = vec(xp11 + w, yp11 + h, 0)

                xp12 = xp11
                yp12 = yp9
                p12 = vec(xp12 + w, yp12 + h, 0)

                xp13 = W - xp8
                yp13 = yp8
                p13 = vec(xp13 + w, yp13 + h, 0)

                xp14 = W - xp7
                yp14 = yp7
                p14 = vec(xp14 + w, yp14 + h, 0)

                xp15 = W - xp6
                yp15 = yp6
                p15 = vec(xp15 + w, yp15 + h, 0)

                xp16 = W - xp5
                yp16 = yp5
                p16 = vec(xp16 + w, yp16 + h, 0)

                xp17 = W - xp4
                yp17 = yp4
                p17 = vec(xp17 + w, yp17 + h, 0)

                xp18 = W - xp3
                yp18 = yp3
                p18 = vec(xp18 + w, yp18 + h, 0)

                xp19 = W - xp2
                yp19 = yp2
                p19 = vec(xp19 + w, yp19 + h, 0)

                xp20 = W
                yp20 = 0
                p20 = vec(xp20 + w, yp20 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                L5 = Part.makeLine(p9, p10)
                L6 = Part.makeLine(p10, p11)
                L7 = Part.makeLine(p11, p12)
                L8 = Part.makeLine(p13, p14)
                L9 = Part.makeLine(p15, p16)
                L10 = Part.makeLine(p17, p18)
                L11 = Part.makeLine(p19, p20)
                L12 = Part.makeLine(p20, p1)

                wire1 = Part.Wire([L1, A1, L2, A2, L3, A3, L4, A4, L5, L6, L7, A5, L8, A6, L9, A7, L10, A8, L11, L12])

            p = Part.Face(wire1)

        if self.fam == "Round bar" or self.fam == "Pipe":
            c = vec(H / 2 + w, H / 2 + h, 0)
            A1 = Part.makeCircle(H / 2, c, d, 0, 360)
            A2 = Part.makeCircle((H - TW) / 2, c, d, 0, 360)
            wire1 = Part.Wire([A1])
            wire2 = Part.Wire([A2])
            if TW:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)

        if L:
            ProfileFull = p.extrude(vec(0, 0, L))
            obj.Shape = ProfileFull

            if B1Y or B2Y or B1X or B2X or B1Z or B2Z:  # make the bevels:

                hc = 10 * max(H, W)

                ProfileExt = ProfileFull.fuse(p.extrude(vec(0, 0, L + hc / 4)))
                box = Part.makeBox(hc, hc, hc)
                box.translate(vec(-hc / 2 + w, -hc / 2 + h, L))
                pr = vec(0, 0, L)
                box.rotate(pr, vec(0, 1, 0), B2Y)
                if self.bevels_combined == True:
                    box.rotate(pr, vec(0, 0, 1), B2Z)
                else:
                    box.rotate(pr, vec(1, 0, 0), B2X)
                ProfileCut = ProfileExt.cut(box)

                ProfileExt = ProfileCut.fuse(p.extrude(vec(0, 0, -hc / 4)))
                box = Part.makeBox(hc, hc, hc)
                box.translate(vec(-hc / 2 + w, -hc / 2 + h, -hc))
                pr = vec(0, 0, 0)
                box.rotate(pr, vec(0, 1, 0), B1Y)
                if self.bevels_combined == True:
                    box.rotate(pr, vec(0, 0, 1), B1Z)
                else:
                    box.rotate(pr, vec(1, 0, 0), B1X)
                ProfileCut = ProfileExt.cut(box)

                obj.Shape = ProfileCut.removeSplitter()

                # if wire2: obj.Shape = Part.Compound([wire1,wire2])  # OCC Sweep doesn't be able hollow shape yet :-(

        else:
            obj.Shape = Part.Face(wire1)
        obj.Placement = pl
        obj.positionBySupport()
        obj.recompute()


def listing_families(lib_path):
    """
    Search families of profiles in profiles library file (Profiles.txt).
    Return a list of profiles families names.
    """
    tab = []
    pos = 0
    file_len = os.stat(lib_path).st_size
    with open(lib_path, "r") as file:
        while pos < file_len:
            while True:
                car = file.read(1)
                if car == "*" or not car: break
            
            line = file.readline()
            txt = line[:len(line) - 1]
            if txt: tab.append(txt)
            line = file.readline()
            line = file.readline()
            line = file.readline()
            pos = file.tell()
            txt = ""
    return tab


def search_txt(lib_path, pos, txt):
    """
    Finds a str from pos
    Returns the new position
    """
    with open(lib_path, "r") as file:
        file.seek(pos)
        while True:
            line = file.readline()
            if line.find(txt) != -1: break
        pos_line = file.tell() - len(line)
        pos_found = pos_line + line.find(txt)
    return pos_found


def extract_data(lib_path, fam, size):
    """
    Extract all data for one dimension of a family
    Return a list:
    Family/Size/Data1/Data2...
    """
    tab = []
    tab.append(fam)
    tab.append(size)
    posfam = search_txt(lib_path, 0, fam)
    possize = search_txt(lib_path, posfam, size)
    car = str = ""

    with open(lib_path, "r") as file:
        file.seek(possize + len(size))
        while True:
            while True:
                car = file.read(1)
                if car == "\t" or car == "\n": break
                str += car
            if str: tab.append(str)
            str = ""
            if car == "\n": break
    return tab


def search_index(lib_path, fam, prop):
    """
    Finds the index of the data in the family
    """
    pos1 = search_txt(lib_path, 0, fam)
    pos2 = search_txt(lib_path, pos1 + 1, "*")
    pos3 = search_txt(lib_path, pos2 + 1, "*")
    pos4 = search_txt(lib_path, pos3 + 1, "*")
    typ = []

    with open(lib_path, "r") as file:
        file.seek(pos4)
        line = file.readline().rstrip()
        typ = line.split("/")
        ind = typ.index(prop) + 1
    return ind


def listing_family_dimensions(lib_path, fam):
    """
    Searches for all dimensions in a family
    And returns a list containing them
    """

    pos1 = search_txt(lib_path, 0, fam)
    pos2 = search_txt(lib_path, pos1 + 1, "*")
    pos3 = search_txt(lib_path, pos2 + 1, "*")
    pos4 = search_txt(lib_path, pos3 + 1, "*")
    tab = []
    str = ""
    with open(lib_path, "r") as file:
        file.seek(pos4)
        line = file.readline()
        car = file.read(1)
        while car != "\n" and car != "":
            while car != "\t":
                str += car
                car = file.read(1)
            if str: tab.append(str)
            str = ""
            line = file.readline()
            car = file.read(1)
    return tab

class _CommandWarehouseProfiles:
    def __init__(self):
        self.p = App.ParamGet("User parameter:BaseApp/Preferences/Mod/metalwb")
        pass

    def GetResources(self):
        """
        Tool resources
        """
        from freecad.metalwb import ICONPATH
        return {
            "Pixmap": os.path.join(ICONPATH, "warehouse_profiles.svg"),
            "MenuText": QT_TRANSLATE_NOOP("StarterKit", "WarehouseProfiles"),
            "Accel": "C, B",
            "ToolTip": "<html><head/><body><p><b>Ajouter des profilés.</b> \
                    <br><br> \
                    </p></body></html>",
        }

    def IsActive(self):
        """
        Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional.
        """
        active = False
        if App.ActiveDocument:
            active = True
        return active

    def Activated(self):
        """
        Define what happen when the user clic on the tool
        """
        print("Warehouse profiles tool activated")
        self.lib_path = self.p.GetString("lib_path")
        if self.lib_path == '':
            self.lib_path = os.path.join(RESOURCESPATH, "Profiles.txt")
        form = Box(self.lib_path)
        Gui.Selection.clearSelection()
        obs = SelObserver(form)
        Gui.Selection.addObserver(obs)
        Gui.Selection.addSelectionGate('SELECT Part::Feature SUBELEMENT Edge')
        form.show()
        form.exec_()
        Gui.Selection.removeObserver(obs)
        Gui.Selection.removeSelectionGate()


if App.GuiUp:
    Gui.addCommand("WarehouseProfiles", _CommandWarehouseProfiles())
