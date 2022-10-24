# coding: utf-8

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
        return txt
    def QT_TRANSLATE_NOOP(ctxt, txt):
        return txt
    # \endcond

__title__ = "FCTreeView"
__author__ = "Mario52"
__url__ = "http://www.freecadweb.org/index-fr.html"
__Wiki__ = "http://www.freecadweb.org/wiki/index.php?title=Macro_FCTreeView"
__version__ = "00.09"
__date__ = "2020/09/24"  # YYYY/MM/DD

import WebGui

import PySide2
from PySide2 import (QtWidgets, QtCore, QtGui)
from PySide2.QtWidgets import (QWidget, QApplication, QSlider, QGraphicsView, QGraphicsScene, QVBoxLayout, QStyle)
from PySide2.QtGui import (QPainter, QColor, QIcon)
from PySide2.QtSvg import *
import PySide2.QtXml

import math
import time
from pivy import coin

import copy  # pour copier 2 tableaux
import re
import time
import operator
from operator import itemgetter, attrgetter, methodcaller  # pour sort

####
# from PySide import QtCore
# global langue
# s=QtCore.QLocale()
# s.countryToString(s.country())
# s.name()
# langue = s.languageToString(s.language())
# print s.name()   # fr
# print langue     # French
####

global ui;
ui = ""
global doc;
doc = ""
global sourisPass;
sourisPass = 0
global listeObjetsOriginal;
listeObjetsOriginal = [
    []]  # objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]
global listeSorted;
listeSorted = [
    []]  # objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]
global listeByStringSear;
listeByStringSear = []  # object searched
global titre;
titre = " Original"
global derouler;
derouler = 0
global visibilite;
visibilite = 0
global group;
group = 0
global searchString;
searchString = ""
global SplitNameLabel;
SplitNameLabel = 0
global selections;
selections = 0

global reverse_00;
reverse_00 = 0
global reverse_01;
reverse_01 = 0
global reverse_02;
reverse_02 = 0
global reverse_03;
reverse_03 = 0

global impost;
impost = ["Angle", "Angle0", "Angle1", "Angle2", "Angle3", "ChamferSize", "Circumradius", "Columns", "Degree",
          "FilletRadius", "FirstAngle", "Growth", "Height", "LastAngle", "Length", "Length2", "MajorRadius",
          "MinorRadius", "Pitch", "Polygon", "Radius", "Radius1", "Radius2", "Radius3", "Rows", "Size", "Width",
          "X", "X1", "X2", "Xmax", "Xmin", "X2max", "X2min",
          "Y", "Y1", "Y2", "Ymax", "Ymin", "Y2max", "Y2min",
          "Z", "Z1", "Z2", "Zmax", "Zmin", "Z2max", "Z2min"]

#### variables global spreadSheet
global densite;
densite = 1.00  # densite / 1d3 (steel) (7.50 kg for 1 dm cube(dm3))
global uniteP;
uniteP = 1.00
global unitePs;
unitePs = "g"
global uniteM;
uniteM = 1.0
global uniteMs;
uniteMs = "mm"
global uniteS;
uniteS = 1.0
global uniteSs;
uniteSs = "mm2"
global uniteV;
uniteV = 1.0
global uniteVs;
uniteVs = "mm3"

global arrondi;
arrondi = 3
global grandeur;
grandeur = ""

global TextColorText_R;
TextColorText_R = 0.627451  # color red   1 = 255
global TextColorText_G;
TextColorText_G = 0.627451  # color green 1 = 255
global TextColorText_B;
TextColorText_B = 0.643137  # color blue  1 = 255
global TextColorText_L;
TextColorText_L = 1.000000  # color blue  1 = 255

global newSpreadSheetName;
newSpreadSheetName = "FCSpreadSheet"
global selectAllCB;
selectAllCB = 0
#### variables global spreadSheet

####################################################################################################
global testing;
testing = 2  # if testing == 1 MainWindow separate


# if testing == 2 RightDock
# else       == other LeftDock
####################################################################################################

def decodeColonne(colonne="A"):  # converti la chaine A ... ZZ en numero de colonne ex: A = 1; AA = 27
    colonne = re.split('[0-9]+', colonne, flags=re.IGNORECASE)[
        0]  # supp the alphanumeric number ex: A2 = A; A12 = A (1A return 0)
    try:
        if len(colonne) > 1:
            return ((ord(colonne[0].upper()) - 64) * 26) + (ord(colonne[1].upper()) - 64)  # max 2 car (AAAA return 27)
        else:
            return (ord(colonne.upper()) - 64)
    except Exception:
        return 0


def decodeOccupation(dataTableau=""):  # decode the max occupation Colonnes, Lines and give the cell occupation
    #
    # lineMax, colonneMax, cellsOccupation = decodeOccupation(FreeCAD.ActiveDocument.getObject(str(Sheet.Name)))
    #
    try:
        tyty = dataTableau.cells.Content
        tyty = tyty.split(">")

        ####
        cellsOccupation = []
        cellsSorted = []  # search the "A1" definition

        for i in tyty[1:-2]:
            i = i[i.find('"') + 1:]  # split les cases dans la chaine XML
            i = i[:i.find('"')]
            if (i[0] >= "A") and (i[0] <= "Z"):  # doit etre une lettre A a Z ( >= 0.18)
                cellsOccupation.append(i)
        cellsSorted = copy.deepcopy(cellsOccupation)
        cellsSorted.sort()
        ####
        linesMax = 0
        for i in cellsSorted:  # recherche le max (ligne et colonne)
            colonnesMax = re.split('[0-9]+', i, flags=re.IGNORECASE)  # colonne max (AA)
            dummy = int(re.split('[A-Z]+', i, flags=re.IGNORECASE)[1])  # line
            if dummy > linesMax:
                linesMax = dummy  # lines max
        del cellsSorted[:]
        ####
        return linesMax, decodeColonne(
            colonnesMax[0]), cellsOccupation  # return linesMax , colonnesMax, cellsOccupation

    except Exception:
        FreeCAD.Console.PrintError("Error data, Enter object <Sheet object> ex:" + "\n")
        FreeCAD.Console.PrintError(
            "lineMax, colonneMax, cellsOccupation = decodeOccupation(FreeCAD.ActiveDocument.getObject(str(Sheet.Name)))" + "\n")
        return 0, 0, []


def caseTableau(ligne=1, colonne=1):  # calcule et code la case du tableur ex caseTableau(1, 2) return B1
    if ligne < 1: ligne = 1
    if ligne > 16384: ligne = 16384
    if colonne < 1: colonne = 1
    if colonne > 702: colonne = 702
    if (colonne > 26):
        if abs(colonne % 26) == 0:
            return chr(64 + (abs(int(colonne / 26)) - 1)) + chr(90) + str(ligne)
        else:
            return chr(64 + (abs(int(colonne / 26)))) + chr(64 + (abs(colonne % 26))) + str(ligne)
    else:
        return chr(colonne + 64) + str(ligne)


def arround(x):
    global arrondi

    return round(x, arrondi)


def affDim(obj, model):
    global grandeur

    objMm = 0.0
    grandeur = ""

    try:
        if model == "Angle":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Angle
        elif model == "Angle0":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Angle0
        elif model == "Angle1":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Angle1
        elif model == "Angle2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Angle2
        elif model == "Angle3":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Angle3
        elif model == "ChamferSize":
            objMm = FreeCAD.ActiveDocument.getObject(obj).ChamferSize
        elif model == "Circumradius":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Circumradius
        elif model == "Columns":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Columns
        elif model == "Degree":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Degree
        elif model == "FilletRadius":
            objMm = FreeCAD.ActiveDocument.getObject(obj).FilletRadius
        elif model == "FirstAngle":
            objMm = FreeCAD.ActiveDocument.getObject(obj).FirstAngle
        elif model == "Growth":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Growth
        elif model == "Height":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Height
        elif model == "LastAngle":
            objMm = FreeCAD.ActiveDocument.getObject(obj).LastAngle
        elif model == "Length":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Length
        elif model == "Length2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Length2
        elif model == "MajorRadius":
            objMm = FreeCAD.ActiveDocument.getObject(obj).MajorRadius
        elif model == "MinorRadius":
            objMm = FreeCAD.ActiveDocument.getObject(obj).MinorRadius
        elif model == "Pitch":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Pitch
        elif model == "Polygon":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Polygon
        elif model == "Radius":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Radius
        elif model == "Radius1":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Radius1
        elif model == "Radius2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Radius2
        elif model == "Radius3":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Radius3
        elif model == "Rotations":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Rotations
        elif model == "Rows":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Rows
        elif model == "Size":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Size
        elif model == "Width":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Width
        elif model == "X":
            objMm = FreeCAD.ActiveDocument.getObject(obj).X
        elif model == "X1":
            objMm = FreeCAD.ActiveDocument.getObject(obj).X1
        elif model == "X2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).X2
        elif model == "X2max":
            objMm = FreeCAD.ActiveDocument.getObject(obj).X2max
        elif model == "X2min":
            objMm = FreeCAD.ActiveDocument.getObject(obj).X2min
        elif model == "Xmax":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Xmax
        elif model == "Xmin":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Xmin
        elif model == "Y":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Y
        elif model == "Y1":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Y1
        elif model == "Y2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Y2
        elif model == "Ymax":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Ymax
        elif model == "Ymin":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Ymin
        elif model == "Z":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Z
        elif model == "Z1":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Z1
        elif model == "Z2":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Z2
        elif model == "Z2max":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Z2max
        elif model == "Z2min":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Z2min
        elif model == "Zmax":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Zmax
        elif model == "Zmin":
            objMm = FreeCAD.ActiveDocument.getObject(obj).Zmin

        try:
            grandeur = str(objMm).split(" ")
            grandeur = grandeur[1]
        except:
            grandeur = ""

        try:
            objMm = objMm.Value
        except:
            objMm = 0.0

    except:
        objMm = 0.0
    return objMm


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class Ui_MainWindow(object):

    def __init__(self, MainWindow):

        self.window = MainWindow
        #############
        # self.path  = FreeCAD.ConfigGet("AppHomePath")
        # self.path  = FreeCAD.ConfigGet("UserAppData")
        # self.path  = "your path"
        param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Macro")  # macro path
        self.path = param.GetString("MacroPath", "") + "/"  # macro path
        self.path = self.path.replace("\\", "/")
        #        print "Path for the icons : " , self.path
        #############

        self.iconName = QtGui.QIcon(self.path + "Macro_FCTreeView_00.png")
        self.iconTrue = QtGui.QIcon(self.path + "Macro_FCTreeView_01.png")
        self.iconFalse = QtGui.QIcon(self.path + "Macro_FCTreeView_02.png")
        self.iconChain = QtGui.QIcon(self.path + "Macro_FCTreeView_03.png")
        self.iconChainCut = QtGui.QIcon(self.path + "Macro_FCTreeView_04.png")
        self.iconLabel = QtGui.QIcon(self.path + "Macro_FCTreeView_05.png")
        self.iconVisible = QtGui.QIcon(self.path + "Macro_FCTreeView_06.png")
        self.iconPaChain = QtGui.QIcon(self.path + "Macro_FCTreeView_07.png")
        self.iconFolder = QtGui.QIcon(self.path + "Macro_FCTreeView_17.png")

    #        self.vueActive = FreeCADGui.ActiveDocument.ActiveView
    #        self.click = self.vueActive.addEventCallback("SoMouseButtonEvent",self.souris)

    #    def souris(self,info):
    #        global sourisPass
    #        #print "ok2"
    #        ##{'ShiftDown': False, 'Button': 'BUTTON1', 'CtrlDown': False, 'State': 'UP', 'Time': 'Sunday, July 23, 2017 21:43:39', 'Position': (479, 354), 'AltDown': False, 'Type': 'SoMouseButtonEvent'}
    #        if (info["Button"] == "BUTTON1") and (info["State"] == "DOWN"):
    #            sourisPass = 0
    #            #print "ok3"
    #

    def setupUi(self, MainWindow):
        global testing
        global densite

        self.window = MainWindow

        if testing == 1:
            MainWindow.setObjectName(_fromUtf8("MainWindow"))  # volant
            MainWindow.resize(340, 600)
        #            MainWindow.setMinimumSize(QtCore.QSize(341,619))
        #            MainWindow.setMaximumSize(QtCore.QSize(341,619))
        #            MainWindow.move(1300, 120)                           # deplace la fenetre

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setMinimumSize(QtCore.QSize(340, 400))

        ######### Layout Header ########################################################################
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")

        self.grid_Principal = QtWidgets.QGridLayout(self.centralwidget)
        self.grid_Principal.setContentsMargins(0, 0, 0, 0)
        self.grid_Principal.setObjectName("grid_Principal")

        self.horizontal_Fenetre = QtWidgets.QHBoxLayout()
        ######### Layout Header ########################################################################

        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        # self.treeWidget.setGeometry(QtCore.QRect(10, 10, 321, 400))     # volant
        #        self.treeWidget.setGeometry(QtCore.QRect(10, 25, 321, 361))     # normal
        # self.treeWidget.setSortingEnabled(True)                         #sort by clicked title
        # __sortingEnabled = self.treeWidget.isSortingEnabled()           #sort by clicked title
        # self.treeWidget.setSortingEnabled(__sortingEnabled)             #sort by clicked title
        # self.treeWidget.header().setSortIndicatorShown(True)            #sort by clicked title

        self.treeWidget.setLineWidth(6)
        self.treeWidget.setDefaultDropAction(QtCore.Qt.CopyAction)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setIconSize(QtCore.QSize(12, 12))  # icon dimensions
        self.treeWidget.setAnimated(True)
        self.treeWidget.header().sectionSize(1200)
        self.treeWidget.header().setDefaultSectionSize(1200)
        self.treeWidget.header().setMinimumSectionSize(1200)  # dimension fenetre interne
        self.treeWidget.header().setCascadingSectionResizes(True)
        self.treeWidget.header().setHighlightSections(True)
        self.treeWidget.header().setStretchLastSection(True)
        #        self.treeWidget.header().setMovable(True)
        self.treeWidget.clicked.connect(self.on_treeWidget_clicked)  # connect on_treeWidget_clicked

        # self.groupBox_Sort = QtWidgets.QGroupBox()

        self.PB_Sort_00 = QtWidgets.QPushButton()
        self.PB_Sort_00.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_10.png"))
        self.PB_Sort_00.clicked.connect(self.on_PB_Sort_00_clicked)

        self.PB_Sort_01 = QtWidgets.QPushButton()
        self.PB_Sort_01.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_11.png"))
        self.PB_Sort_01.clicked.connect(self.on_PB_Sort_01_clicked)

        self.PB_Sort_02 = QtWidgets.QPushButton()
        self.PB_Sort_02.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_12.png"))
        self.PB_Sort_02.clicked.connect(self.on_PB_Sort_02_clicked)

        self.PB_Sort_03 = QtWidgets.QPushButton()
        self.PB_Sort_03.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_13.png"))
        self.PB_Sort_03.clicked.connect(self.on_PB_Sort_03_clicked)

        self.CB_Length = QtWidgets.QCheckBox()
        self.CB_Length.setChecked(False)
        self.CB_Length.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_19.png"))

        # self.groupBox_Global = QtWidgets.QGroupBox()

        #        self.PB_Reverse = QtWidgets.QPushButton()
        #        self.PB_Reverse.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_08.png"))
        #        self.PB_Reverse.clicked.connect(self.on_PB_Reverse_clicked)

        self.PB_SplitName = QtWidgets.QPushButton()
        self.PB_SplitName.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_22.png"))
        self.PB_SplitName.clicked.connect(self.on_PB_SplitName_clicked)

        self.PB_Expend = QtWidgets.QPushButton()
        self.PB_Expend.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_15.png"))
        self.PB_Expend.clicked.connect(self.on_PB_Expend_clicked)

        self.PB_Visibility = QtWidgets.QPushButton()
        self.PB_Visibility.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_06.png"))
        self.PB_Visibility.clicked.connect(self.on_PB_Visibility_clicked)

        self.PB_Group = QtWidgets.QPushButton()
        self.PB_Group.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_07.png"))
        self.PB_Group.clicked.connect(self.on_PB_Group_clicked)

        self.PB_Reload = QtWidgets.QPushButton()
        self.PB_Reload.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_16.png"))
        self.PB_Reload.clicked.connect(self.on_PB_Reload_clicked)

        self.PB_Original = QtWidgets.QPushButton()
        self.PB_Original.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_18.png"))
        self.PB_Original.clicked.connect(self.on_PB_Original_clicked)

        self.PB_All_Visible = QtWidgets.QPushButton()
        self.PB_All_Visible.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_01.png"))
        self.PB_All_Visible.clicked.connect(self.on_PB_All_Visible_clicked)

        self.PB_All_Hidden = QtWidgets.QPushButton()
        self.PB_All_Hidden.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_02.png"))
        self.PB_All_Hidden.clicked.connect(self.on_PB_All_Hidden_clicked)

        # self.groupBox_Search = QtWidgets.QGroupBox()

        self.lineEdit_Search = QtWidgets.QLineEdit()
        #        self.lineEdit_Search.returnPressed.connect(self.on_lineEdit_Search_Pressed)      # for validate the data with press on return touch
        self.lineEdit_Search.textChanged.connect(self.on_lineEdit_Search_Pressed)  # with tips key char by char

        self.PB_ClearLEdit = QtWidgets.QPushButton()
        self.PB_ClearLEdit.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_20.png"))
        self.PB_ClearLEdit.clicked.connect(self.on_PB_ClearLEdit_clicked)

        self.frame_Options = QtWidgets.QFrame()
        self.frame_Options.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_Options.setFrameShadow(QtWidgets.QFrame.Plain)

        self.RB_01_NameLabel = QtWidgets.QRadioButton()
        self.RB_01_NameLabel.setChecked(True)
        self.RB_01_NameLabel.clicked.connect(self.on_RB_Pressed)

        self.RB_02_Name_CS = QtWidgets.QRadioButton()
        self.RB_02_Name_CS.clicked.connect(self.on_RB_Pressed)

        self.RB_03_Label_NC = QtWidgets.QRadioButton()
        self.RB_03_Label_NC.clicked.connect(self.on_RB_Pressed)

        self.RB_04_NamLabel_CS = QtWidgets.QRadioButton()
        self.RB_04_NamLabel_CS.clicked.connect(self.on_RB_Pressed)

        self.RB_05_NameLabel_AL = QtWidgets.QRadioButton()
        self.RB_05_NameLabel_AL.clicked.connect(self.on_RB_Pressed)

        self.RB_06_Numeric_Num = QtWidgets.QRadioButton()
        self.RB_06_Numeric_Num.clicked.connect(self.on_RB_Pressed)

        self.PB_Select = QtWidgets.QPushButton()
        self.PB_Select.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_23.png"))
        self.PB_Select.clicked.connect(self.on_PB_Select_clicked)

        self.ComboB_Type = QtWidgets.QComboBox()
        self.ComboB_Type.addItem(_fromUtf8(""))
        #        self.ComboB_Type.currentIndexChanged.connect(self.SIGNAL_ComboB_Type_Changed)
        self.ComboB_Type.activated.connect(self.SIGNAL_ComboB_Type_Changed)

        self.label_Ver = QtWidgets.QLabel()

        self.PB_SpreadSheet = QtWidgets.QPushButton()
        self.PB_SpreadSheet.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_25.png"))
        self.PB_SpreadSheet.clicked.connect(self.on_PB_SpreadSheet_clicked)

        self.PB_Quit = QtWidgets.QPushButton()
        self.PB_Quit.setVisible(False)

        if testing == 1:  # 1=MainWindow separate
            MainWindow.setCentralWidget(self.centralwidget)
            MainWindow.setWindowTitle(__title__ + u" (" + __version__ + " rmu (" + __date__ + "))")

            self.PB_Quit.setVisible(True)
            self.PB_Quit.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_09.png"))
            self.PB_Quit.setText("Quit")
            self.PB_Quit.setToolTip("Quit FCTreeView <img src=" + self.path + "Macro_FCTreeView_09.png" + " />")
            self.PB_Quit.clicked.connect(self.on_PB_Quit_clicked)
        else:
            MainWindow.setWidget(self.centralwidget)
            MainWindow.setWindowTitle(__title__ + u" (" + __version__ + " rmu)")
            # MainWindow.setWindowTitle(__title__ + u" (" + __version__ + " rmu) modified")

        ####SpreadSheet begin#######

        self.Frame_Contener_SpreadSheet = QtWidgets.QGroupBox()
        self.Frame_Contener_SpreadSheet.setVisible(False)

        self.Frame_01_SpreadSheet = QtWidgets.QFrame()
        self.Frame_01_SpreadSheet.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame_01_SpreadSheet.setFrameShadow(QtWidgets.QFrame.Raised)

        self.CB_01_Title = QtWidgets.QCheckBox()
        self.CB_01_Title.setChecked(True)
        self.CB_01_Title.clicked.connect(self.on_CB_01_Title_clicked)

        self.CB_02_Color = QtWidgets.QCheckBox()
        self.CB_02_Color.setChecked(True)
        self.CB_02_Color.clicked.connect(self.on_CB_02_Color_clicked)

        self.CB_03_Colonne = QtWidgets.QCheckBox()
        self.CB_03_Colonne.setChecked(True)

        self.CB_04_Name = QtWidgets.QCheckBox()

        self.CB_05_Label = QtWidgets.QCheckBox()
        self.CB_05_Label.setChecked(True)

        self.CB_06_Nomenclature = QtWidgets.QCheckBox()
        self.CB_06_Nomenclature.clicked.connect(self.on_CB_06_Nomenclature_clicked)

        self.CB_07_Solid = QtWidgets.QCheckBox()

        self.CB_08_Volume = QtWidgets.QCheckBox()

        self.CB_09_Weight = QtWidgets.QCheckBox()

        self.CB_10_Weight_Total = QtWidgets.QCheckBox()
        self.CB_10_Weight_Total.setEnabled(False)

        self.CB_11_Surface = QtWidgets.QCheckBox()

        self.CB_12_BBox = QtWidgets.QCheckBox()

        self.CB_13_Translate = QtWidgets.QCheckBox()

        self.CB_14_Rotation = QtWidgets.QCheckBox()

        self.CB_15_Dimension = QtWidgets.QCheckBox()
        self.CB_15_Dimension.setChecked(True)

        # self.LA_Wait = QtWidgets.QLabel()

        self.progressBar_01 = QtWidgets.QProgressBar()
        self.progressBar_01.setMaximum(100)
        self.progressBar_01.setMinimum(0)
        self.progressBar_01.setValue(0)
        self.progressBar_01.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar_01.setAlignment(QtCore.Qt.AlignCenter)
        # self.progressBar_01.setToolTip(_translate("MainWindow", "progressBar_01", None))

        self.Frame_02_SpreadSheet = QtWidgets.QFrame()
        self.Frame_02_SpreadSheet.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame_02_SpreadSheet.setFrameShadow(QtWidgets.QFrame.Plain)

        self.RB_01_Value = QtWidgets.QRadioButton()
        self.RB_01_Value.setChecked(True)

        self.RB_02_Val_Gr = QtWidgets.QRadioButton()

        self.RB_03_Val_Gr_Ph = QtWidgets.QRadioButton()

        self.CB_08_Split = QtWidgets.QCheckBox()

        self.Frame_03_Config = QtWidgets.QFrame()
        self.Frame_03_Config.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame_03_Config.setFrameShadow(QtWidgets.QFrame.Plain)

        self.CBox_01_Longueur = QtWidgets.QComboBox()
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        self.CBox_01_Longueur.addItem(_fromUtf8(""))
        # self.CBox_01_Longueur.currentIndexChanged.connect(self.On_ComboB_SpreadSheet)    # donne le num de ligne
        self.CBox_01_Longueur.currentIndexChanged[str].connect(self.On_CBox_01_Longueur_SpreadSheet)  # [str] or [int]

        self.CBox_02_Poids = QtWidgets.QComboBox()
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        self.CBox_02_Poids.addItem(_fromUtf8(""))
        # self.CBox_02_Poids.currentIndexChanged.connect(self.On_ComboB_SpreadSheet)    # donne le num de ligne
        self.CBox_02_Poids.activated[str].connect(self.On_CBox_02_Poids_SpreadSheet)  # [str] or [int]

        self.DS_01_Densite = QtWidgets.QDoubleSpinBox()
        self.DS_01_Densite.setSuffix(" Density")
        self.DS_01_Densite.setMinimum(-9999999999.999)
        self.DS_01_Densite.setMaximum(999.999)
        self.DS_01_Densite.setDecimals(4)
        self.DS_01_Densite.setValue(densite)
        self.DS_01_Densite.setSingleStep(1)
        self.DS_01_Densite.valueChanged.connect(self.on_DS_01_Densite_valueChanged)

        self.DS_02_Round = QtWidgets.QSpinBox()
        self.DS_02_Round.setMinimum(0)
        self.DS_02_Round.setMaximum(40)
        self.DS_02_Round.setValue(3)
        self.DS_02_Round.setSingleStep(1)
        self.DS_02_Round.valueChanged.connect(self.on_DS_02_Round_valueChanged)

        self.ComboB_SpreadSheet = QtWidgets.QComboBox()
        # self.ComboB_SpreadSheet.addItem(_fromUtf8(""))
        # self.ComboB_SpreadSheet.currentIndexChanged.connect(self.On_ComboB_SpreadSheet)    # donne le num de ligne
        self.ComboB_SpreadSheet.currentIndexChanged[str].connect(self.On_ComboB_SpreadSheet)  # [str] or [int]

        self.LE_SpreadSheet = QtWidgets.QLineEdit()
        self.LE_SpreadSheet.setText(newSpreadSheetName)
        self.LE_SpreadSheet.textChanged.connect(self.on_LE_SpreadSheet_Pressed)  # connect on "on_LE_SpreadSheet_Pressed

        self.PB_01_SpreadSheet_Select_All = QtWidgets.QPushButton()
        self.PB_01_SpreadSheet_Select_All.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_28.png"))
        self.PB_01_SpreadSheet_Select_All.clicked.connect(self.on_PB_01_SpreadSheet_Select_All_clicked)

        self.PB_03_SpreadSheet_Save = QtWidgets.QPushButton()
        self.PB_03_SpreadSheet_Save.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_27.png"))
        self.PB_03_SpreadSheet_Save.clicked.connect(self.on_PB_03_SpreadSheet_Save_clicked)

        self.PB_04_SpreadSheet_Quit = QtWidgets.QPushButton()
        self.PB_04_SpreadSheet_Quit.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_26.png"))
        self.PB_04_SpreadSheet_Quit.clicked.connect(self.on_PB_04_SpreadSheet_Quit_clicked)

        ####SpreadSheet end######
        ######### Layout Begin ########################################################################
        self.horizontal_Fenetre.addWidget(self.treeWidget)
        self.horizontal_Fenetre.setContentsMargins(10, 5, 10, 0)
        self.grid_Principal.addLayout(self.horizontal_Fenetre, 1, 0, 1, 1)
        self.horizontal_Group_Sort_By = QtWidgets.QHBoxLayout()
        #### Sort
        ####
        self.groupBox_Sort = QtWidgets.QGroupBox(self.gridLayoutWidget)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(self.groupBox_Sort)
        self.grid_Bouton_SortBy = QtWidgets.QGridLayout(self.groupBox_Sort)
        self.grid_Bouton_SortBy.setContentsMargins(10, 10, 10, 10)
        self.grid_Bouton_SortBy.addWidget(self.PB_Sort_00, 0, 0, 1, 1)
        self.grid_Bouton_SortBy.addWidget(self.PB_Sort_01, 0, 1, 1, 1)
        self.grid_Bouton_SortBy.addWidget(self.PB_Sort_02, 0, 2, 1, 1)
        self.grid_Bouton_SortBy.addWidget(self.PB_Sort_03, 0, 3, 1, 1)
        self.grid_Bouton_SortBy.addWidget(self.CB_Length, 0, 4, 1, 1)

        self.horizontal_Group_Sort_By.addWidget(self.groupBox_Sort)
        self.grid_Principal.addLayout(self.horizontal_Group_Sort_By, 2, 0, 1, 1)
        self.horizontal_Group_Sort_By.setContentsMargins(10, 5, 10, 0)  # marge
        self.horizontal_Group_Global = QtWidgets.QHBoxLayout()
        ####
        ####
        #### Global
        ####
        self.groupBox_Global = QtWidgets.QGroupBox(self.gridLayoutWidget)
        self.gridLayoutWidget_3 = QtWidgets.QWidget(self.groupBox_Global)
        self.gridLayoutWidget_3.setContentsMargins(10, 5, 10, 10)

        self.grid_Global_Boutons = QtWidgets.QGridLayout(self.groupBox_Global)

        self.horizontal_Group_Global.addWidget(self.groupBox_Global)
        self.horizontal_Group_Global.setContentsMargins(10, 5, 10, 0)
        #        self.grid_Global_Boutons.setContentsMargins(10, 10, 10, 10)
        self.grid_Global_Boutons.addWidget(self.PB_SplitName, 0, 0, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_Expend, 0, 1, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_Visibility, 0, 2, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_Group, 0, 3, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_Reload, 1, 0, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_Original, 1, 1, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_All_Visible, 1, 2, 1, 1)
        self.grid_Global_Boutons.addWidget(self.PB_All_Hidden, 1, 3, 1, 1)

        self.grid_Principal.addLayout(self.horizontal_Group_Global, 3, 0, 1, 1)
        ####
        ####
        #### Search
        ####
        self.horizontal_GroupBox_Search = QtWidgets.QHBoxLayout()
        self.horizontal_GroupBox_Search.setContentsMargins(10, 0, 10, 10)
        self.groupBox_Search = QtWidgets.QGroupBox(self.gridLayoutWidget)
        self.groupBox_Search.setContentsMargins(10, 5, 10, 10)
        self.grid_Boutons_Search = QtWidgets.QGridLayout(self.groupBox_Search)
        self.grid_Boutons_Search.setContentsMargins(10, 10, 10, 10)

        self.grid_Boutons_Search.addWidget(self.lineEdit_Search, 0, 0, 1, 2)
        self.grid_Boutons_Search.addWidget(self.PB_ClearLEdit, 0, 2, 1, 1)
        self.grid_Boutons_Search.addWidget(self.ComboB_Type, 2, 0, 1, 1)
        # self.grid_Boutons_Search.addWidget(self.PB_Select, 1, 2, 1, 1)
        self.grid_Boutons_Search.addWidget(self.PB_SpreadSheet, 2, 1, 1, 1)
        self.frame_Options = QtWidgets.QFrame(self.groupBox_Search)
        self.frame_Options.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_Options.setFrameShadow(QtWidgets.QFrame.Plain)
        self.grid_Search_Radio_Bouton = QtWidgets.QGridLayout(self.frame_Options)
        self.gridLayoutWidget_5 = QtWidgets.QWidget(self.frame_Options)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_01_NameLabel, 0, 0, 1, 1)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_02_Name_CS, 0, 1, 1, 1)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_03_Label_NC, 0, 2, 1, 1)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_04_NamLabel_CS, 0, 3, 1, 1)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_05_NameLabel_AL, 0, 4, 1, 1)
        self.grid_Search_Radio_Bouton.addWidget(self.RB_06_Numeric_Num, 0, 5, 1, 1)
        if testing == 1:
            self.grid_Boutons_Search.addWidget(self.PB_Select, 1, 2, 1, 1)
            self.grid_Boutons_Search.addWidget(self.PB_Quit, 2, 2, 1, 1)
            self.grid_Boutons_Search.addWidget(self.frame_Options, 1, 0, 1, 2)
        else:
            self.grid_Boutons_Search.addWidget(self.PB_Select, 2, 2, 1, 1)
            self.grid_Boutons_Search.addWidget(self.frame_Options, 1, 0, 1, 3)

        self.horizontal_GroupBox_Search.addWidget(self.groupBox_Search)
        self.grid_Principal.addLayout(self.horizontal_GroupBox_Search, 4, 0, 1, 1)
        ####
        ####
        #### SpreedSheet
        ####
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(10, 5, 10, 0)
        self.Frame_Contener_SpreadSheet = QtWidgets.QGroupBox(self.gridLayoutWidget)
        self.Frame_Contener_SpreadSheet.setVisible(False)

        self.gridLayoutWidget_6 = QtWidgets.QWidget(self.Frame_Contener_SpreadSheet)
        ####
        self.gridLayout_23 = QtWidgets.QGridLayout(self.Frame_Contener_SpreadSheet)
        self.gridLayout_23.setContentsMargins(10, 10, 10, 10)
        self.gridLayout_20 = QtWidgets.QGridLayout()

        ####
        self.gridLayout_20.addWidget(self.CB_01_Title, 0, 0, 1, 1)
        self.gridLayout_20.addWidget(self.CB_02_Color, 0, 1, 1, 1)
        self.gridLayout_20.addWidget(self.CB_03_Colonne, 0, 2, 1, 1)
        self.gridLayout_20.addWidget(self.CB_04_Name, 0, 3, 1, 1)
        self.gridLayout_20.addWidget(self.CB_05_Label, 0, 4, 1, 1)
        self.gridLayout_20.addWidget(self.CB_06_Nomenclature, 1, 0, 1, 1)
        self.gridLayout_20.addWidget(self.CB_07_Solid, 1, 1, 1, 1)
        self.gridLayout_20.addWidget(self.CB_08_Volume, 1, 2, 1, 1)
        self.gridLayout_20.addWidget(self.CB_09_Weight, 1, 3, 1, 1)
        self.gridLayout_20.addWidget(self.CB_10_Weight_Total, 1, 4, 1, 1)
        self.gridLayout_20.addWidget(self.CB_11_Surface, 2, 0, 1, 1)
        self.gridLayout_20.addWidget(self.CB_12_BBox, 2, 1, 1, 1)
        self.gridLayout_20.addWidget(self.CB_13_Translate, 2, 2, 1, 1)
        self.gridLayout_20.addWidget(self.CB_14_Rotation, 2, 3, 1, 1)
        self.gridLayout_20.addWidget(self.CB_15_Dimension, 2, 4, 1, 1)
        # self.gridLayout_20.addWidget(self.LA_Wait, x, x, 1, 1)

        ####
        self.Frame_02_SpreadSheet = QtWidgets.QFrame(self.gridLayoutWidget_6)
        self.Frame_02_SpreadSheet.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame_02_SpreadSheet.setFrameShadow(QtWidgets.QFrame.Plain)

        ####
        self.gridLayout_21 = QtWidgets.QGridLayout(self.Frame_02_SpreadSheet)
        self.gridLayout_21.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_21.addWidget(self.RB_01_Value, 0, 0, 1, 1)
        self.gridLayout_21.addWidget(self.RB_02_Val_Gr, 0, 1, 1, 1)
        self.gridLayout_21.addWidget(self.RB_03_Val_Gr_Ph, 0, 2, 1, 1)
        self.gridLayout_21.addWidget(self.CB_08_Split, 0, 3, 1, 1)
        ####

        self.gridLayout_20.addWidget(self.Frame_02_SpreadSheet, 7, 0, 1, 5)

        self.gridLayout_20.addWidget(self.CBox_01_Longueur, 8, 0, 1, 1)
        self.gridLayout_20.addWidget(self.CBox_02_Poids, 8, 1, 1, 2)
        self.gridLayout_20.addWidget(self.DS_01_Densite, 8, 3, 1, 1)
        self.gridLayout_20.addWidget(self.DS_02_Round, 8, 4, 1, 1)

        self.gridLayout_20.addWidget(self.ComboB_SpreadSheet, 9, 0, 1, 3)
        self.gridLayout_20.addWidget(self.LE_SpreadSheet, 9, 3, 1, 2)

        self.gridLayout_20.addWidget(self.progressBar_01, 6, 0, 1, 5)
        self.gridLayout_23.addLayout(self.gridLayout_20, 0, 0, 1, 1)
        ####

        self.Frame_03_Config = QtWidgets.QFrame(self.gridLayoutWidget_6)
        self.Frame_03_Config.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame_03_Config.setFrameShadow(QtWidgets.QFrame.Plain)

        ####
        self.gridLayoutWidget_8 = QtWidgets.QWidget(self.Frame_03_Config)

        self.gridLayout_22 = QtWidgets.QGridLayout(self.Frame_03_Config)
        self.gridLayout_22.setContentsMargins(5, 5, 5, 5)

        self.gridLayout_22.addWidget(self.PB_01_SpreadSheet_Select_All, 0, 0, 1, 1)
        self.gridLayout_22.addWidget(self.PB_03_SpreadSheet_Save, 0, 1, 1, 1)
        self.gridLayout_22.addWidget(self.PB_04_SpreadSheet_Quit, 0, 2, 1, 1)

        self.gridLayout_23.addWidget(self.Frame_03_Config, 1, 0, 1, 1)

        self.gridLayout.addWidget(self.Frame_Contener_SpreadSheet, 0, 0, 1, 1)
        self.grid_Principal.addLayout(self.gridLayout, 3, 0, 1, 1)
        ####
        ####
        ######### Layout End ########################################################################

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        if testing == 1:
            MainWindow.setCentralWidget(self.centralwidget)

    def retranslateUi(self, MainWindow):
        global newSpreadSheetName

        MainWindow.setWindowIcon(
            QtGui.QIcon(self.path + "Macro_FCTreeView_18.png"))  # change l'icone de la fenetre principale
        MainWindow.setWindowFlags(
            PySide2.QtCore.Qt.WindowStaysOnTopHint)  # PySide cette fonction met la fenetre en avant

        self.treeWidget.setToolTip("The title display the option, number and type object(s) displayed" + "\n" + "\n" +
                                   "O = Objects" + "\n" +
                                   "N = Name" + "\n" +
                                   "L = Label" + "\n" +
                                   "Nu= Numeric" + "\n" +
                                   "T = Total" + "\n" +
                                   "G = Group" + "\n" +
                                   "S = Single" + "\n" +
                                   "V = Visible" + "\n" +
                                   "H = Hidden" + "\n\n" +
                                   "If one object are selected :" + "\n" +
                                   "the Placement Base, Rotation and Center of mass is displayed" + "\n" +
                                   "if available !")

        self.groupBox_Sort.setTitle("Sort by:")
        self.PB_Sort_00.setText("Name")
        self.PB_Sort_00.setToolTip("<img src=" + self.path + "Macro_FCTreeView_10.png" + " />" + "\n" +
                                   "Sort by <b>Name</b>")
        self.PB_Sort_01.setText("Label")
        self.PB_Sort_01.setToolTip("<img src=" + self.path + "Macro_FCTreeView_11.png" + " />" + "\n" +
                                   "Sort by <b>Label</b>")
        self.PB_Sort_02.setText("Visible")
        self.PB_Sort_02.setToolTip("<img src=" + self.path + "Macro_FCTreeView_12.png" + " />" + "\n" +
                                   "Sort by <b>Visibility</b>")
        self.PB_Sort_03.setText("Group")
        self.PB_Sort_03.setToolTip("<img src=" + self.path + "Macro_FCTreeView_13.png" + " />" + "\n" +
                                   "Sort by <b>Group</b>")
        self.CB_Length.setText("Length")
        self.CB_Length.setToolTip("<img src=" + self.path + "Macro_FCTreeView_19.png" + " />" + "\n" +
                                  "If Checked sort by string length")

        self.groupBox_Global.setTitle("Global")
        #        self.PB_Reverse.setText("Reverse")
        #        self.PB_Reverse.setToolTip("<img src=" + self.path + "Macro_FCTreeView_08.png" + " />" + "\n" +
        #                                   "Reverse the data listing")
        self.PB_SplitName.setText("Split")
        self.PB_SplitName.setToolTip("<img src=" + self.path + "Macro_FCTreeView_22.png" + " />" + "\n" +
                                     "Split name and label")
        self.PB_Expend.setText("Expend")
        self.PB_Expend.setToolTip("<img src=" + self.path + "Macro_FCTreeView_15.png" + " />" + "\n" +
                                  "Expend the listing objects")
        self.PB_Visibility.setText("Visibility")
        self.PB_Visibility.setToolTip("<img src=" + self.path + "Macro_FCTreeView_06.png" + " />" + "\n" +
                                      "The first icon display the visibility or not")
        self.PB_Group.setText("Group")
        self.PB_Group.setToolTip("<img src=" + self.path + "Macro_FCTreeView_07.png" + " />" + "\n" +
                                 "The first icon display the group or not")
        self.PB_Reload.setText("Reload")
        self.PB_Reload.setToolTip("<img src=" + self.path + "Macro_FCTreeView_16.png" + " />" + "\n" +
                                  "Reload the <b>ACTUAL VIEW</b> on 3D Screen")
        self.PB_Original.setText("Original")
        self.PB_Original.setToolTip("<img src=" + self.path + "Macro_FCTreeView_18.png" + " />" + "\n" +
                                    "Return to original objects organisation and visibility")
        self.PB_All_Visible.setText("All Visible")
        self.PB_All_Visible.setToolTip("<img src=" + self.path + "Macro_FCTreeView_01.png" + " />" + "\n" +
                                       "All objects Visible" + "\n" +
                                       "For restitute the original organisation click to <b>Original</b> button" + "\n" +
                                       " <img src=" + self.path + "Macro_FCTreeView_18.png" + " />")
        self.PB_All_Hidden.setText("All Hidden")
        self.PB_All_Hidden.setToolTip("<img src=" + self.path + "Macro_FCTreeView_02.png" + " />" + "\n" +
                                      "All objects Hidden" + "\n" +
                                      "For restitute the original organisation click to <b>Original</b> button" + "\n" +
                                      "<img src=" + self.path + "Macro_FCTreeView_18.png" + " />")

        self.groupBox_Search.setTitle("Search")
        self.PB_ClearLEdit.setText("Clear")
        self.PB_ClearLEdit.setToolTip(
            "Clear the Line Search same lineEdit emptied <img src=" + self.path + "Macro_FCTreeView_20.png" + " />")

        self.RB_01_NameLabel.setText("NLwc")
        self.RB_01_NameLabel.setToolTip("Search by Name and Label Without respecting the sensitive Case")
        self.RB_02_Name_CS.setText("Nsc")
        self.RB_02_Name_CS.setToolTip("Search by Name and respecting the Sensitive Case")
        self.RB_03_Label_NC.setText("Lwc")
        self.RB_03_Label_NC.setToolTip("Search by Label Without respecting the sensitive Case")
        self.RB_04_NamLabel_CS.setText("NLsc")
        self.RB_04_NamLabel_CS.setToolTip("Search by Name and Label and respecting the Sensitive Case")
        self.RB_05_NameLabel_AL.setText("NLwsc")
        self.RB_05_NameLabel_AL.setToolTip("Search by Name and Label in Word and respecting the Sensitive Case" + "\n" +
                                           "(same panel selection of FreeCAD)")
        self.RB_06_Numeric_Num.setText("Num")
        self.RB_06_Numeric_Num.setToolTip("Search by Numeric value" + "\n" +
                                          "The value searched is the absolute value" + "\n" +
                                          " ex: entry 10" + "\n" +
                                          " result: 10, 10.5, 10.2154...")
        self.ComboB_Type.setToolTip("Search the object by type")

        self.PB_SpreadSheet.setText("S Sheet")
        self.PB_SpreadSheet.setToolTip("<img src=" + self.path + "Macro_FCTreeView_25.png" + " />" + "\n" +
                                       "SpreadSheet options")

        if testing == 1:
            self.PB_Quit.setText("Quit")
            self.PB_Quit.setToolTip("<img src=" + self.path + "Macro_FCTreeView_09.png" + " />" + "\n" +
                                    "Quit FCTreeView")
            self.label_Ver.setText("FCTreeView (" + __version__ + " (" + __date__ + "))")

        self.PB_Select.setText("Select")
        self.PB_Select.setToolTip(
            "Select all object(s) displayed <img src=" + self.path + "Macro_FCTreeView_23.png" + " />")

        self.ComboB_Type.setItemText(0, "Choice your type")

        ########SpreadSheet##
        self.Frame_Contener_SpreadSheet.setTitle("SpreadSheet")

        self.Frame_01_SpreadSheet.setToolTip("options to save in a spreadSheet")

        self.CB_01_Title.setText("Title")
        self.CB_01_Title.setToolTip("Create title align Centered and Bold")
        self.CB_02_Color.setText("Color cell")
        self.CB_02_Color.setToolTip("Colored the complete title in Grey" + "\n" +
                                    "(Background)")
        self.CB_03_Colonne.setText("Column")
        self.CB_03_Colonne.setToolTip("Colored the column Value of object in Grey" + "\n" +
                                      "If Color is checked")
        self.CB_04_Name.setText("Name")
        self.CB_04_Name.setToolTip("Real name of the object")
        self.CB_05_Label.setText("Label")
        self.CB_05_Label.setToolTip("Label of object")

        self.CB_06_Nomenclature.setText("Nomenclature")
        self.CB_06_Nomenclature.setToolTip("Nomenclature of object create a listing" + "\n" +
                                           "and display number part(s)" + "\n" +
                                           "in case of same Label the test is done on the volume" + "\n" +
                                           "to detect if the objects are identical" + "\n" +
                                           "(option available : W.Total)")
        self.CB_07_Solid.setText("Solid")
        self.CB_07_Solid.setToolTip("Type object Solid")
        self.CB_08_Volume.setText("Volume")
        self.CB_08_Volume.setToolTip("Calculate the Volume object" + "\n" +
                                     "(single object)")
        self.CB_09_Weight.setText("Weight")
        self.CB_09_Weight.setToolTip("Calculate the Weight object" + "\n" +
                                     "The weigth object is convert in the unit selected" + "\n" +
                                     "(single object)")
        self.CB_10_Weight_Total.setText("W.Total")
        self.CB_10_Weight_Total.setToolTip("Calculate the Weight total of object(s)" + "\n" +
                                           "This option is available if the Nomenclature is checked" + "\n" +
                                           "The weigth object(s) is convert in the unit selected")

        self.CB_11_Surface.setText("Surface")
        self.CB_11_Surface.setToolTip("Calculate the Surface of object" + "\n" +
                                      "The Surface object is convert in the unit selected" + "\n" +
                                      "(single object)")
        self.CB_12_BBox.setText("BBox")
        self.CB_12_BBox.setToolTip("Calculate the BoundBox of object" + "\n" +
                                   "The BoundBox value is convert in the unit selected")
        self.CB_13_Translate.setText("Translat.")
        self.CB_13_Translate.setToolTip("Display the Placement Translation values of object" + "\n" +
                                        "The Translation value is convert in the unit selected")
        self.CB_14_Rotation.setText("Rotation")
        self.CB_14_Rotation.setToolTip("Display the Placement Rotation values of object" + "\n" +
                                       "The Rotation value is convert in Degrees")
        self.CB_15_Dimension.setText("Dim.")
        self.CB_15_Dimension.setToolTip("Display the other Dimensions... values of object" + "\n" +
                                        "The Dimensions value is convert :" + "\n" +
                                        "in unit selected, in Degrees" + "\n" +
                                        "or none if the value is numerical value (ex:number face)" + "\n" +
                                        "The number of value depend of the object")

        self.Frame_02_SpreadSheet.setToolTip("Frame SpreadSheet Values" + "\n" +
                                             "Value     = value of object" + "\n" +
                                             "Val Gr    = value + unit detected (in same cell)" + "\n" +
                                             "Val Gr Ph = value + unit + type detected (in same cell)" + "\n" +
                                             "Split     = split the value group in cell separate")

        self.RB_01_Value.setText("Value")
        self.RB_01_Value.setToolTip("<img src=" + self.path + "Macro_FCTreeView_30.png" + " />" + "\n" +
                                    "Value = value of object" + "\n" +
                                    " ( Ex: 10.50 )")
        self.RB_02_Val_Gr.setText("Val Gr")
        self.RB_02_Val_Gr.setToolTip("<img src=" + self.path + "Macro_FCTreeView_31.png" + " />" + "\n" +
                                     "Val Gr = value + unit detected (in same cell)" + "\n" +
                                     " ( Ex: 10.50 mm )")
        self.RB_03_Val_Gr_Ph.setText("Val Gr Ph")
        self.RB_03_Val_Gr_Ph.setToolTip("<img src=" + self.path + "Macro_FCTreeView_32.png" + " />" + "\n" +
                                        "Val Gr Ph = value + unit + type detected (in same cell)" + "\n" +
                                        " ( Ex: 10.50 mm Length )")
        self.CB_08_Split.setText("Split")
        self.CB_08_Split.setToolTip("<img src=" + self.path + "Macro_FCTreeView_33.png" + " />" + "\n" +
                                    "Split = split the value group in cell separate" + "\n" +
                                    " ( Ex: 10.50 , mm , Length )")

        # http://fr.wikipedia.org/wiki/Unit%C3%A9s_de_mesure_anglo-saxonnes
        self.CBox_01_Longueur.setToolTip("Unit on choice" + "\n" + "Unit by default = mm")
        self.CBox_01_Longueur.setCurrentIndex(6)
        self.CBox_01_Longueur.setItemText(0, "km")  # km #        = 1000000
        self.CBox_01_Longueur.setItemText(1, "hm")  # hm #        = 100000
        self.CBox_01_Longueur.setItemText(2, "dam")  # dam#        = 10000
        self.CBox_01_Longueur.setItemText(3, "m")  # m  #        = 1000
        self.CBox_01_Longueur.setItemText(4, "dm")  # dm #        = 100
        self.CBox_01_Longueur.setItemText(5, "cm")  # cm #        = 10
        self.CBox_01_Longueur.setItemText(6, "mm")  # mm #        = 1
        self.CBox_01_Longueur.setItemText(7, "um")  # um #        = 0.001            micro
        self.CBox_01_Longueur.setItemText(8, "nm")  # nm # *      = 0.000001         nano
        self.CBox_01_Longueur.setItemText(9, "pm")  # pm #        = 0.000000001      pico
        self.CBox_01_Longueur.setItemText(10, "fm")  # fm #        = 0.000000000001   femto
        self.CBox_01_Longueur.setItemText(11, "inch")  # in # inch  pouce    = 25.400
        self.CBox_01_Longueur.setItemText(12, "link")  # lk # link  chainon  = 201.168
        self.CBox_01_Longueur.setItemText(13, "foot")  # ft # foot  pied     = 304.800
        self.CBox_01_Longueur.setItemText(14, "yard")  # yd # yard  verge    = 914.400
        self.CBox_01_Longueur.setItemText(15, "perch")  # rd # rod ou perch   perche   = 5029.200
        self.CBox_01_Longueur.setItemText(16, "chain")  # ch # chain chaine   = 20116.800
        self.CBox_01_Longueur.setItemText(17, "furlong")  # fur# furlong        = 201168
        self.CBox_01_Longueur.setItemText(18, "mile")  # mi # mile           = 1609344
        self.CBox_01_Longueur.setItemText(19, "league")  # lea# league lieue   = 4828032
        self.CBox_01_Longueur.setItemText(20, "nautique")  # nmi# mile nautique  = 1852000

        self.CBox_02_Poids.setToolTip("Unit on choice for Density on dm3" + "\n" + "Unit by default = g")
        self.CBox_02_Poids.setCurrentIndex(5)
        self.CBox_02_Poids.setItemText(0, "tonne")  # t    #   = 1000000
        self.CBox_02_Poids.setItemText(1, "quintal")  # q    #   = 100000
        self.CBox_02_Poids.setItemText(2, "kilo gram")  # kg   #   = 1000
        self.CBox_02_Poids.setItemText(3, "hecto gram")  # hg   #   = 100
        self.CBox_02_Poids.setItemText(4, "decagram")  # dag  #   = 10
        self.CBox_02_Poids.setItemText(5, "gram")  # g    #   = 1
        self.CBox_02_Poids.setItemText(6, "decigram")  # dg   #   = 0.1
        self.CBox_02_Poids.setItemText(7, "centigram")  # cg   #   = 0.01
        self.CBox_02_Poids.setItemText(8, "milligram")  # mg   #   = 0.001
        self.CBox_02_Poids.setItemText(9, "microgram")  # µg   #   = 0.000001
        self.CBox_02_Poids.setItemText(10, "nanogram")  # ng   #   = 0.000000001
        self.CBox_02_Poids.setItemText(11, "picogram")  # pg   #   = 0.000000000001
        self.CBox_02_Poids.setItemText(12, "femtogram")  # fg   #   = 0.000000000000001   femtogram
        self.CBox_02_Poids.setItemText(13, "grain")  # gr   #   = 0.06479891 g
        self.CBox_02_Poids.setItemText(14, "drachm")  # dr   #   = 1.7718451953125 g
        self.CBox_02_Poids.setItemText(15, "once")  # oz   #   = 28.3495231250 g
        self.CBox_02_Poids.setItemText(16, "once troy")  # oz t #   = 31.1034768 g  once troy
        self.CBox_02_Poids.setItemText(17, "livre troy")  # lb t #   = 373.2417216 g  livre de troy
        self.CBox_02_Poids.setItemText(18, "livre av")  # lb   #   = 453.59237 g  livre avoirdupois pound
        self.CBox_02_Poids.setItemText(19, "stone")  # st   #   = 6350.29318 g
        self.CBox_02_Poids.setItemText(20, "quarter")  # qtr  #   = 12700.58636 g
        self.CBox_02_Poids.setItemText(21, "hundredweight")  # cwt  #   = 50802.34544 g
        self.CBox_02_Poids.setItemText(22, "tonneau fr")  # #   = 0.00000102145045965 g
        self.CBox_02_Poids.setItemText(23, "carat")  # ct   #   = 0.2 g

        self.DS_01_Densite.setToolTip("Density of material used" + "\n" +
                                      "By default = 1.0 kg by dm3")
        self.DS_02_Round.setToolTip("Number of decimal value used" + "\n" +
                                    "By default = 3")
        self.ComboB_SpreadSheet.setToolTip("List the spreadSheet available")
        self.LE_SpreadSheet.setToolTip("SpreadSheet current (first displayed)" + "\n" +
                                       "If there is no spreadSheet in the document," + "\n" +
                                       "one spreadSheet named FCSpreadSheet is created" + "\n" +
                                       "or the spreadSheet displayed is updated" + "\n" +
                                       "or enter your spreadSheet name")
        self.PB_01_SpreadSheet_Select_All.setText("Select")
        self.PB_01_SpreadSheet_Select_All.setToolTip(
            "<img src=" + self.path + "Macro_FCTreeView_28.png" + " />" + "\n" +
            "Select all checkBox options")
        self.PB_03_SpreadSheet_Save.setText("Save")
        self.PB_03_SpreadSheet_Save.setToolTip("<img src=" + self.path + "Macro_FCTreeView_27.png" + " />" + "\n" +
                                               "Save the data in SpreadSheet" + "\n" +
                                               "( actual = " + "<b>" + newSpreadSheetName + "</b>" + " )")
        self.PB_04_SpreadSheet_Quit.setText("Quit")
        self.PB_04_SpreadSheet_Quit.setToolTip("<img src=" + self.path + "Macro_FCTreeView_26.png" + " />" + "\n" +
                                               "Quit the SpreadSheet module")
        ########SpreadSheet##

    def details(self, type, name):  # details object
        if type == 0:
            Fdoc = FreeCAD.ActiveDocument.getObject(name)
        else:
            Fdoc = FreeCAD.ActiveDocument.getObjectsByLabel(name)[0]
        try:
            Bx = ("Base\nX : " + str(round(Fdoc.Placement.Base[0], 3)) + "\n")
            By = ("Y : " + str(round(Fdoc.Placement.Base[1], 3)) + "\n")
            Bz = ("Z : " + str(round(Fdoc.Placement.Base[2], 3)) + "\n\n")
            base = Bx + By + Bz
        except Exception:
            base = ""
        try:
            Rx = ("Rotation\nX : " + str(round(Fdoc.Placement.Rotation.toEuler()[0], 3)) + "\n")
            Ry = ("Y : " + str(round(Fdoc.Placement.Rotation.toEuler()[1], 3)) + "\n")
            Rz = ("Z : " + str(round(Fdoc.Placement.Rotation.toEuler()[2], 3)) + "\n\n")
            rotation = Rx + Ry + Rz
        except Exception:
            rotation = ""
        try:
            Cx = ("CenterOfMass\nX : " + str(round(Fdoc.Shape.CenterOfMass[0], 3)) + "\n")
            Cy = ("Y : " + str(round(Fdoc.Shape.CenterOfMass[1], 3)) + "\n")
            Cz = ("Z : " + str(round(Fdoc.Shape.CenterOfMass[2], 3)) + "\n\n")
            centerOfMass = Cx + Cy + Cz
        except Exception:
            centerOfMass = ""
        return name[:20] + "\n\n" + base + rotation + centerOfMass

    def on_treeWidget_clicked(self, item):
        global listeObjetsOriginal
        global titre
        global ui
        global doc
        global searchString

        ligne = item.row()  # index dans la liste
        colonne = item.column()  # index dans la liste
        nomObjetListe = item.data()  # donne le nom clique
        nomParentBase = item.parent().data()  # donne le nom du maitre

        try:
            if (nomObjetListe == "False") or (nomObjetListe == "True"):
                if nomObjetListe == "False":
                    try:
                        FreeCAD.ActiveDocument.getObject(nomParentBase).ViewObject.Visibility = True
                    except Exception:
                        App.ActiveDocument.getObjectsByLabel(nomParentBase)[0].ViewObject.Visibility = True
                else:
                    try:
                        FreeCAD.ActiveDocument.getObject(nomParentBase).ViewObject.Visibility = False
                    except Exception:
                        App.ActiveDocument.getObjectsByLabel(nomParentBase)[0].ViewObject.Visibility = False

                if searchString == " Searched":
                    ui.loadObjects()
                    ui.on_lineEdit_Search_Pressed()
                else:
                    ui.on_PB_Reload_clicked()

            FreeCADGui.Selection.clearSelection()
            if nomParentBase == doc:
                try:
                    FreeCADGui.Selection.addSelection(App.ActiveDocument.getObject(nomObjetListe))
                    self.treeWidget.setToolTip(ui.details(0, nomObjetListe))
                except Exception:
                    FreeCADGui.Selection.addSelection(App.ActiveDocument.getObjectsByLabel(nomObjetListe)[0])
                    self.treeWidget.setToolTip(ui.details(1, nomObjetListe))
            else:
                try:
                    FreeCADGui.Selection.addSelection(App.ActiveDocument.getObject(nomParentBase))
                    self.treeWidget.setToolTip(ui.details(0, nomParentBase))
                except Exception:
                    # ver 0.19 Gui.Selection.addSelection(App.ActiveDocument.Name,selection.Name,vertex, x, y, z)
                    print(nomParentBase)
                    FreeCADGui.Selection.addSelection(App.ActiveDocument.getObjectsByLabel(nomParentBase)[0])
                    self.treeWidget.setToolTip(ui.details(1, nomParentBase))

            # zoom_selection # https://forum.freecadweb.org/viewtopic.php?f=8&t=15132
            Gui.SendMsgToActiveView("ViewSelection")
            Gui.runCommand("Std_TreeSelection")

        except Exception:
            self.treeWidget.setToolTip(
                "The title display the option, number and type object(s) displayed" + "\n" + "\n" +
                "O = Objects" + "\n" +
                "N = Name" + "\n" +
                "L = Label" + "\n" +
                "T = Total" + "\n" +
                "G = Group" + "\n" +
                "S = Single" + "\n" +
                "V = Visible" + "\n" +
                "H = Hidden" + "\n\n" +
                "If one object are selected :" + "\n" +
                "the Placement Base, Rotation and Center of mass is displayed" + "\n" +
                "if available !")
            FreeCAD.Console.PrintError("Error clicked" + "\n")

    def sorted_List(self, option):  # listing after sorted
        global doc
        global listeSorted
        global titre
        global derouler
        global visibilite
        global group
        global SplitNameLabel

        enteteTitres = QtWidgets.QTreeWidgetItem([" Sorted" + option, ])  # titres entete des colonnes
        self.treeWidget.setHeaderItem(
            enteteTitres)  # affichage des titres #Another alternative is setHeaderLabels(["Tree","First",...])
        documentActif = QtWidgets.QTreeWidgetItem(self.treeWidget, [str(doc)])  # titre du document
        documentActif.setExpanded(True)  # expent tous les enfants

        #       #[objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]
        for obj in listeSorted:

            if (SplitNameLabel == 0) or (SplitNameLabel == 1):
                A = QtWidgets.QTreeWidgetItem(documentActif, [obj[0]])  # premier objet dans l'arbre du document
                if obj[3] == "-":
                    A.setIcon(0, self.iconName)  # premiere rangee titre
                else:
                    A.setIcon(0, self.iconFolder)  # premiere rangee titre

                if derouler == 1:
                    A.setExpanded(True)  # expent tous les enfants

                etat = QtWidgets.QTreeWidgetItem(A)
                if obj[-1] == 1:  # convert firt char lower original
                    objL = obj[1][0].lower() + obj[1][1:]
                    etat.setText(0, objL)  # label
                else:
                    etat.setText(0, obj[1])  # label
                etat.setIcon(0, self.iconLabel)

                etat2 = QtWidgets.QTreeWidgetItem(A)
                if obj[2] == "True":
                    etat2.setText(0, "True")  # premiere rangee
                    etat2.setIcon(0, self.iconTrue)  # premiere rangee
                    if visibilite == 1:
                        A.setIcon(0, self.iconTrue)  # premiere rangee titre
                else:
                    etat2.setText(0, "False")  # premiere rangee
                    etat2.setIcon(0, self.iconFalse)  # premiere rangee
                    if visibilite == 1:
                        A.setIcon(0, self.iconFalse)  # premiere rangee titre

                etat3 = QtWidgets.QTreeWidgetItem(A)
                if obj[3] == "-":
                    if group == 1:
                        A.setIcon(0, self.iconChainCut)  # premiere rangee titre
                    None
                else:
                    etat3.setText(0, obj[3])
                    etat3.setIcon(0, self.iconChain)  # premiere rangee
                    if group == 1:
                        A.setIcon(0, self.iconChain)  # premiere rangee titre

            if (SplitNameLabel == 1) or (SplitNameLabel == 2):
                A = QtWidgets.QTreeWidgetItem(documentActif, [obj[1]])  # premier objet dans l'arbre du document
                if obj[-1] == 1:  # convert firt char lower original
                    objL = obj[1][0].lower() + obj[1][1:]
                    A.setText(0, objL)  # label
                else:
                    A.setText(0, obj[1])  # label
                A.setIcon(0, self.iconLabel)  # premiere rangee titre

                if derouler == 1:
                    A.setExpanded(True)  # expent tous les enfants

                B = QtWidgets.QTreeWidgetItem(A)
                if obj[3] == "-":
                    B.setIcon(0, self.iconName)  # premiere rangee titre
                else:
                    B.setIcon(0, self.iconFolder)  # premiere rangee titre
                B.setText(0, obj[0])  # name

                C = QtWidgets.QTreeWidgetItem(A)
                if obj[2] == "True":
                    C.setText(0, "True")  # premiere rangee
                    C.setIcon(0, self.iconTrue)  # premiere rangee
                    if visibilite == 1:
                        A.setIcon(0, self.iconTrue)  # premiere rangee titre
                else:
                    C.setText(0, "False")  # premiere rangee
                    C.setIcon(0, self.iconFalse)  # premiere rangee
                    if visibilite == 1:
                        A.setIcon(0, self.iconFalse)  # premiere rangee titre

                D = QtWidgets.QTreeWidgetItem(A)
                if obj[3] == "-":
                    if group == 1:
                        A.setIcon(0, self.iconChainCut)  # premiere rangee titre
                    None
                else:
                    D.setText(0, obj[3])
                    D.setIcon(0, self.iconChain)  # premiere rangee
                    if group == 1:
                        A.setIcon(0, self.iconChain)  # premiere rangee titre

    def on_PB_Sort_00_clicked(self):  # tableau 0 Nom
        global listeSorted
        global ui
        global titre
        global reverse_00
        global reverse_01
        global reverse_02
        global reverse_03

        #       #[objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]
        if self.CB_Length.isChecked():
            listeSorted = sorted(listeSorted, key=itemgetter(4))
            titre = " by Length Name"
        else:
            listeSorted = sorted(listeSorted, key=itemgetter(0))
            titre = " by Name"
        self.treeWidget.clear()
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

        if reverse_00 == 1:
            ui.on_PB_Reverse_clicked()
            reverse_00 = 0
        else:
            reverse_00 = 1
        reverse_01 = reverse_02 = reverse_03 = 0
        self.treeWidget.verticalScrollBar().setStyleSheet("background-color: #0000ce;")

    def on_PB_Sort_01_clicked(self):  # tableau 1 Label
        global listeSorted
        global ui
        global titre
        global reverse_00
        global reverse_01
        global reverse_02
        global reverse_03

        #       #[objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]

        if self.CB_Length.isChecked():
            listeSorted = sorted(listeSorted, key=itemgetter(5))
            titre = " by Length Label"
        else:
            listeSorted = sorted(listeSorted, key=itemgetter(1))
            titre = " by Label"
        self.treeWidget.clear()
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

        if reverse_01 == 1:
            ui.on_PB_Reverse_clicked()
            reverse_01 = 0
        else:
            reverse_01 = 1
        reverse_00 = reverse_02 = reverse_03 = 0
        self.treeWidget.verticalScrollBar().setStyleSheet("background-color: #0073cc;")

    def on_PB_Sort_02_clicked(self):  # tableau 2 False True
        global listeSorted
        global ui
        global titre
        global reverse_00
        global reverse_01
        global reverse_02
        global reverse_03

        self.treeWidget.clear()
        listeSorted = sorted(listeSorted, key=itemgetter(2))
        titre = " by Visibility"
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

        if reverse_02 == 1:
            ui.on_PB_Reverse_clicked()
            reverse_02 = 0
            self.treeWidget.verticalScrollBar().setStyleSheet("background-color: #007000;")
        else:
            reverse_02 = 1
            self.treeWidget.verticalScrollBar().setStyleSheet("background-color: #cc0000;")
        reverse_00 = reverse_01 = reverse_03 = 0

    def on_PB_Sort_03_clicked(self):  # tableau 3 False Groupe premier niveau
        global listeSorted
        global ui
        global titre
        global reverse_00
        global reverse_01
        global reverse_02
        global reverse_03

        if self.CB_Length.isChecked():
            listeSorted = sorted(listeSorted, key=itemgetter(6))
            titre = " by Length Group"
        else:
            listeSorted = sorted(listeSorted, key=itemgetter(3))
            titre = " by Group"
        self.treeWidget.clear()
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

        if reverse_03 == 1:
            ui.on_PB_Reverse_clicked()
            reverse_03 = 0
        else:
            reverse_03 = 1
        reverse_00 = reverse_01 = reverse_02 = 0
        self.treeWidget.verticalScrollBar().setStyleSheet("background-color: #ff5555;")

    def on_PB_Reverse_clicked(self):  # reverse tableau
        global listeSorted
        global ui
        global titre

        listeSorted.reverse()
        self.treeWidget.clear()
        if titre[-9:] == " reverse>":
            titre = titre.replace(">", "<")
        elif titre[-9:] == " reverse<":
            titre = titre.replace("<", ">")
        else:
            titre += " reverse<"
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    def on_PB_SplitName_clicked(self):  # Split Name and Label
        global ui
        global titre
        global SplitNameLabel
        global listeSorted

        if SplitNameLabel == 0:
            self.PB_SplitName.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_05.png"))
            self.PB_SplitName.setToolTip("<img src=" + self.path + "Macro_FCTreeView_05.png" + " />" + "\n" +
                                         "Display by Label")
            SplitNameLabel = 1
        elif SplitNameLabel == 1:
            self.PB_SplitName.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_17.png"))
            self.PB_SplitName.setToolTip("<img src=" + self.path + "Macro_FCTreeView_17.png" + " />" + "\n" +
                                         "Display by Name")
            SplitNameLabel = 2
        else:
            self.PB_SplitName.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_22.png"))
            self.PB_SplitName.setToolTip("<img src=" + self.path + "Macro_FCTreeView_22.png" + " />" + "\n" +
                                         "Display by Name and Label")
            SplitNameLabel = 0

        self.treeWidget.clear()
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    def on_PB_Expend_clicked(self):
        global ui
        global titre
        global derouler
        global listeSorted

        if derouler == 1:
            derouler = 0
            self.PB_Expend.setText("Develop")
            self.PB_Expend.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_15.png"))
            self.PB_Expend.setToolTip(
                "Click for Develop the listing objects <img src=" + self.path + "Macro_FCTreeView_15.png" + " />")
        else:
            derouler = 1
            self.PB_Expend.setText("Fold")
            self.PB_Expend.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_14.png"))
            self.PB_Expend.setToolTip(
                "Click for Fold the listing objects <img src=" + self.path + "Macro_FCTreeView_14.png" + " />")

        self.treeWidget.clear()
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    ########SpreadSheet section debut #####################################################################################################
    def On_CBox_01_Longueur_SpreadSheet(self, text):
        global uniteM
        global uniteMs
        global uniteS
        global uniteSs
        global uniteV
        global uniteVs

        #        text = text.encode('utf-8')                         # PySide
        if text == "km":  # = 1000000
            uniteM = 0.000001
            uniteMs = "km"
            uniteS = 0.000000000001
            uniteSs = "km2"
            uniteV = 0.000000000000000001
            uniteVs = "km3"
        elif text == "hm":  # = 100000
            uniteM = 0.00001
            uniteMs = "hm"
            uniteS = 0.0000000001
            uniteSs = "hm2"
            uniteV = 0.000000000000001
            uniteVs = "hm3"
        elif text == "dam":  # = 10000
            uniteM = 0.0001
            uniteMs = "dam"
            uniteS = 0.00000001
            uniteSs = "dam2"
            uniteV = 0.000000000001
            uniteVs = "dam3"
        elif text == "m":  # = 1000
            uniteM = 0.001
            uniteMs = "m"
            uniteS = 0.000001
            uniteSs = "m2"
            uniteV = 0.000000001
            uniteVs = "m3"
        elif text == "dm":  # = 100
            uniteM = 0.01
            uniteMs = "dm"
            uniteS = 0.0001
            uniteSs = "dm2"
            uniteV = 0.000001
            uniteVs = "dm3"
        elif text == "cm":  # = 10
            uniteM = 0.1
            uniteMs = "cm"
            uniteS = 0.01
            uniteSs = "cm2"
            uniteV = 0.001
            uniteVs = "cm3"
        elif text == "mm":  # = 1 ###############################
            uniteM = 1.0
            uniteMs = "mm"
            uniteS = 1.0
            uniteSs = "mm2"
            uniteV = 1.0
            uniteVs = "mm3"
        elif text == "um":  # = 1000 #http://fr.wiktionary.org/wiki/%CE%BCm#conv
            uniteM = 1000.0
            uniteMs = "um"
            uniteS = 1000.0 ** 2
            uniteSs = "um2"
            uniteV = 1000.0 ** 3
            uniteVs = "um3"
        elif text == "nm":  # = 1000000
            uniteM = 1000000.0
            uniteMs = "nm"
            uniteS = 1000000.0 ** 2
            uniteSs = "nm2"
            uniteV = 1000000.0 ** 3
            uniteVs = "nm3"
        elif text == "pm":  # = 1000000000
            uniteM = 1000000000.0
            uniteMs = "pm"
            uniteS = 1000000000.0 ** 2
            uniteSs = "pm2"
            uniteV = 1000000000.0 ** 3
            uniteVs = "pm3"
        elif text == "fm":  # = 1000000000000
            uniteM = 1000000000000.0
            uniteMs = "fm"
            uniteS = 1000000000000.0 ** 2
            uniteSs = "fm2"
            uniteV = 1000000000000.0 ** 3
            uniteVs = "fm3"
        elif text == "inch":  # inch   = 25.400
            uniteM = 1.0 / 25.400
            uniteMs = "in"
            uniteS = uniteM ** 2
            uniteSs = "sq in"
            uniteV = uniteM ** 3
            uniteVs = "in3"
        elif text == "link":  # link   = 201.168
            uniteM = 1.0 / 201.168
            uniteMs = "lk"
            uniteS = uniteM ** 2
            uniteSs = "sq lk"
            uniteV = uniteM ** 3
            uniteVs = "lk3"
        elif text == "foot":  # foot   = 304.800
            uniteM = 1.0 / 304.800
            uniteMs = "ft"
            uniteS = uniteM ** 2
            uniteSs = "sq ft"
            uniteV = uniteM ** 3
            uniteVs = "ft3"
        elif text == "yard":  # yard   = 914.400
            uniteM = 1.0 / 914.400
            uniteMs = "yd"
            uniteS = uniteM ** 2
            uniteSs = "sq yd"
            uniteV = uniteM ** 3
            uniteVs = "yd3"
        elif text == "perch":  # rd # rod   perche    = 5029.200
            uniteM = 1.0 / 5029.200
            uniteMs = "rd"
            uniteS = uniteM ** 2
            uniteSs = "sq rd"
            uniteV = uniteM ** 3
            uniteVs = "rd3"
        elif text == "chain":  # chain  = 20116.800
            uniteM = 1.0 / 20116.800
            uniteMs = "ch"
            uniteS = uniteM ** 2
            uniteSs = "sq ch"
            uniteV = uniteM ** 3
            uniteVs = "ch3"
        elif text == "furlong":  # furlong= 201168
            uniteM = 1.0 / 201168
            uniteMs = "fur"
            uniteS = uniteM ** 2
            uniteSs = "sq fur"
            uniteV = uniteM ** 3
            uniteVs = "fur3"
        elif text == "mile":  # mile   = 1609344
            uniteM = 1.0 / 1609344
            uniteMs = "mi"
            uniteS = uniteM ** 2
            uniteSs = "sq mi"
            uniteV = uniteM ** 3
            uniteVs = "mi3"
        elif text == "league":  # league = 4828032
            uniteM = 1.0 / 4828032
            uniteMs = "lea"
            uniteS = uniteM ** 2
            uniteSs = "sq lea"
            uniteV = uniteM ** 3
            uniteVs = "lea3"
        elif text == "nautique":  # nautique = 1852000
            uniteM = 1.0 / 1852000
            uniteMs = "nmi"
            uniteS = uniteM ** 2
            uniteSs = "sq nmi"
            uniteV = uniteM ** 3
            uniteVs = "nmi3"

    def On_CBox_02_Poids_SpreadSheet(self, text):
        global uniteP
        global unitePs

        # poids = ((volume_ * densite) * uniteP) / 1000)
        #        text = text.encode('utf-8')  # PySide
        if text == "tonne":  # t  #0.000001  = 1000000
            uniteP = 0.000001
            unitePs = "t"
        elif text == "quintal":  # q  #0.00001   = 100000
            uniteP = 0.00001
            unitePs = "q"
        elif text == "kilo gram":  # kg # 0.001    = 1000
            uniteP = 0.001
            unitePs = "kg"
        elif text == "hecto gram":  # hg #  0.01    = 100
            uniteP = 0.01
            unitePs = "hg"
        elif text == "decagram":  # dag#   0.1    = 10
            uniteP = 0.1
            unitePs = "dag"
        elif text == "gram":  # g  #  1       = 1
            uniteP = 1.00
            unitePs = "g"
        elif text == "decigram":  # dg   # = 0.1
            uniteP = 10
            unitePs = "dg"
        elif text == "centigram":  # cg   # = 0.01
            uniteP = 100
            unitePs = "cg"
        elif text == "milligram":  # mg   # = 0.001
            uniteP = 1000
            unitePs = "mg"
        elif text == "microgram":  # µg   # = 0.000001
            uniteP = 1000000
            unitePs = "ug"
        elif text == "nanogram":  # ng   # = 0.000000001
            uniteP = 1000000000
            unitePs = "ng"
        elif text == "picogram":  # pg   # = 0.000000000001
            uniteP = 1000000000000
            unitePs = "pg"
        elif text == "femtogram":  # fg   # = 0.000000000000001
            uniteP = 1000000000000000
            unitePs = "fg"
        elif text == "grain":  # gr   # = 0.06479891
            uniteP = 0.06479891
            unitePs = "gr"
        elif text == "drachm":  # dr   # = 1.7718451953125
            uniteP = 0.56438339189006794681850148894339
            unitePs = "dr"
        elif text == "once":  # oz   # = 28.3495231250
            uniteP = 0.035273961949580412915675808215204
            unitePs = "oz"
        elif text == "once troy":  # oz t # = once troy   = 31.1034768
            uniteP = 0.032150746568627980522100346029483
            unitePs = "oz t"
        elif text == "livre troy":  # lb t # = 373.2417216 livre de troy (pound)
            uniteP = 0.0026792288807189983768416955024569
            unitePs = "lb t"
        elif text == "livre av":  # lb   # = 453.59237   livre avoirdupois (pound)
            uniteP = 0.0022046226218487758072297380134503
            unitePs = "lb"
        elif text == "stone":  # st   # = 6350.29318  1 stone     = 14 livres
            uniteP = 0.00015747304441776970051640985810359
            unitePs = "st"
        elif text == "quarter":  # qtr  # = 12700.58636
            uniteP = 0.000078736522208884850258204929051795
            unitePs = "qtr"
        elif text == "hundredweight":  # cwt  # = 50802.34544
            uniteP = 0.000019684130552221212564551232262949
            unitePs = "cwt"
        elif text == "tonneau fr":  # # tonneau fr = 0.00000102145045965
            uniteP = 0.00000102145045965
            unitePs = "tonneau fr"
        elif text == "carat":  # ct   # = 0.2
            uniteP = 5
            unitePs = "ct"

    def on_DS_01_Densite_valueChanged(self, value):
        global densite

        densite = value

    def on_DS_02_Round_valueChanged(self, value):
        global arrondi

        arrondi = value

    def on_CB_01_Title_clicked(self):
        if self.CB_01_Title.isChecked():
            self.CB_02_Color.setEnabled(True)
        else:
            self.CB_02_Color.setEnabled(False)
            self.CB_03_Colonne.setEnabled(False)
        self.CB_02_Color.setChecked(False)
        self.CB_03_Colonne.setChecked(False)

    def on_CB_02_Color_clicked(self):
        if self.CB_02_Color.isChecked():
            self.CB_03_Colonne.setEnabled(True)
        else:
            self.CB_03_Colonne.setEnabled(False)
            self.CB_03_Colonne.setChecked(False)

    def on_CB_06_Nomenclature_clicked(self):
        if self.CB_06_Nomenclature.isChecked():
            self.CB_06_Nomenclature.setStyleSheet("background-color: white;\n"
                                                  "border:2px solid rgb(115, 210, 22);")  # bord white and green
            self.CB_10_Weight_Total.setStyleSheet("background-color: white;\n"
                                                  "border:2px solid rgb(115, 210, 22);")  # bord white and green
            self.CB_10_Weight_Total.setEnabled(True)
        else:
            self.CB_06_Nomenclature.setStyleSheet("Base")
            self.CB_10_Weight_Total.setStyleSheet("Base")
            self.CB_10_Weight_Total.setEnabled(False)
            self.CB_10_Weight_Total.setChecked(False)

    def on_LE_SpreadSheet_Pressed(self, text):
        global newSpreadSheetName

        newSpreadSheetName = text
        self.PB_03_SpreadSheet_Save.setToolTip("<img src=" + self.path + "Macro_FCTreeView_27.png" + " />" + "\n" +
                                               "Save the data in SpreadSheet" + "\n" +
                                               "( actual = " + "<b>" + newSpreadSheetName + "</b>" + " )")

    def On_ComboB_SpreadSheet(self, text):
        global newSpreadSheetName

        newSpreadSheetName = text
        self.LE_SpreadSheet.setText(newSpreadSheetName)

    def on_PB_04_SpreadSheet_Quit_clicked(self):
        global ui

        self.Frame_Contener_SpreadSheet.setVisible(False)
        self.groupBox_Sort.setVisible(True)
        self.groupBox_Search.setVisible(True)
        self.groupBox_Global.setVisible(True)
        # ui.on_PB_Reload_clicked()    # reload the total objects after spreadSheet but lose the sort

    def on_PB_03_SpreadSheet_Save_clicked(self):
        global ui

        ui.tableauSpreadsheet()
        ui.on_PB_SpreadSheet_clicked()

    def on_PB_01_SpreadSheet_Select_All_clicked(self):
        global selectAllCB

        if selectAllCB == 1:
            self.CB_01_Title.setChecked(False)
            self.CB_02_Color.setChecked(False)
            self.CB_02_Color.setEnabled(False)
            self.CB_03_Colonne.setChecked(False)
            self.CB_03_Colonne.setEnabled(False)
            self.CB_04_Name.setChecked(False)
            self.CB_05_Label.setChecked(False)
            self.CB_06_Nomenclature.setChecked(False)
            self.CB_06_Nomenclature.setStyleSheet("Base")
            self.CB_07_Solid.setChecked(False)
            self.CB_08_Volume.setChecked(False)
            self.CB_09_Weight.setChecked(False)
            self.CB_10_Weight_Total.setChecked(False)
            self.CB_10_Weight_Total.setEnabled(False)
            self.CB_10_Weight_Total.setStyleSheet("Base")
            self.CB_11_Surface.setChecked(False)
            self.CB_12_BBox.setChecked(False)
            self.CB_13_Translate.setChecked(False)
            self.CB_14_Rotation.setChecked(False)
            self.CB_15_Dimension.setChecked(False)
            selectAllCB = 0
            self.PB_01_SpreadSheet_Select_All.setText("Select")
            self.PB_01_SpreadSheet_Select_All.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_28.png"))
            self.PB_01_SpreadSheet_Select_All.setToolTip(
                "<img src=" + self.path + "Macro_FCTreeView_28.png" + " />" + "\n" +
                "Select all checkBox options")
        else:
            self.CB_01_Title.setChecked(True)
            self.CB_02_Color.setChecked(True)
            self.CB_02_Color.setEnabled(True)
            self.CB_03_Colonne.setChecked(True)
            self.CB_03_Colonne.setEnabled(True)
            self.CB_04_Name.setChecked(True)
            self.CB_05_Label.setChecked(True)
            self.CB_06_Nomenclature.setChecked(True)
            self.CB_06_Nomenclature.setStyleSheet("background-color: white;\n"
                                                  "border:2px solid rgb(115, 210, 22);")  # bord white and green
            self.CB_07_Solid.setChecked(True)
            self.CB_08_Volume.setChecked(True)
            self.CB_09_Weight.setChecked(True)
            self.CB_10_Weight_Total.setChecked(True)
            self.CB_10_Weight_Total.setEnabled(True)
            self.CB_10_Weight_Total.setStyleSheet("background-color: white;\n"
                                                  "border:2px solid rgb(115, 210, 22);")  # bord white and green
            self.CB_11_Surface.setChecked(True)
            self.CB_12_BBox.setChecked(True)
            self.CB_13_Translate.setChecked(True)
            self.CB_14_Rotation.setChecked(True)
            self.CB_15_Dimension.setChecked(True)
            selectAllCB = 1
            self.PB_01_SpreadSheet_Select_All.setText("Unselect")
            self.PB_01_SpreadSheet_Select_All.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_29.png"))
            self.PB_01_SpreadSheet_Select_All.setToolTip(
                "<img src=" + self.path + "Macro_FCTreeView_29.png" + " />" + "\n" +
                "UnSelect all checkBox options")

    def on_PB_SpreadSheet_clicked(self):
        global listeSorted

        if len(listeSorted) != 0:
            self.groupBox_Sort.setVisible(False)
            self.groupBox_Search.setVisible(False)
            self.groupBox_Global.setVisible(False)
            self.Frame_Contener_SpreadSheet.setVisible(True)

            self.ComboB_SpreadSheet.clear()
            for i in FreeCAD.ActiveDocument.Objects:  # reload for search all SpreadSheet
                obj = FreeCAD.ActiveDocument.getObject(i.Name).TypeId.split("::")[0]
                if obj == "Spreadsheet":
                    self.ComboB_SpreadSheet.addItem(_fromUtf8(str(i.Name)))
        else:
            self.PB_SpreadSheet.setStyleSheet("background-color: #ef2929; color: rgb(255, 255, 255)")

    def tableauSpreadsheet(self):  # create the SpreadSheet
        global listeSorted
        global ui
        global newSpreadSheetName
        global densite
        global uniteP
        global unitePs
        global uniteM
        global uniteMs
        global uniteS
        global uniteSs
        global uniteV
        global uniteVs
        global grandeur
        global TextColorText_R
        global TextColorText_G
        global TextColorText_B
        global TextColorText_L

        #### section nomenclature avec test sur volume ####
        self.progressBar_01.setMinimum(0)
        self.progressBar_01.setMaximum(len(listeSorted))
        self.progressBar_01.setStyleSheet("QProgressBar {color:black; }"
                                          "QProgressBar:chunk {background-color: #FFA500;}")  # modify the progressBar color
        # self.LA_Wait.setText("Wait sort in progress")

        listeSortedBis = []
        listeSortedBis = copy.deepcopy(listeSorted)
        listeSortedBis = sorted(listeSortedBis, key=itemgetter(1))  # sorted by Label

        if self.CB_06_Nomenclature.isChecked():

            compteurPB = 0
            for doublon in range(len(listeSorted)):
                try:
                    volumeShape1 = str(
                        FreeCAD.ActiveDocument.getObject(listeSortedBis[doublon][0]).Shape.Volume)  # Volume Shape
                except Exception:
                    volumeShape1 = "0.0"
                listeSortedBis[doublon][2] = "1"
                listeSortedBis[doublon][3] = volumeShape1
                compteurPB += 1
                self.progressBar_01.setValue(compteurPB)
            listeSortedBis = sorted(listeSortedBis, key=itemgetter(1, 3))  # sorted by Label and Volume

            try:
                compteurPB = 0
                doublon = 1
                while doublon < len(listeSorted):
                    # if (listeSortedBis[doublon][1] == listeSortedBis[doublon-1][1]): # same Name
                    if (listeSortedBis[doublon][1] == listeSortedBis[doublon - 1][1]) and (
                            listeSortedBis[doublon][3] == listeSortedBis[doublon - 1][3]):  # same Name and Volume
                        listeSortedBis[doublon - 1][2] = str(int(listeSortedBis[doublon - 1][2]) + 1)
                        del listeSortedBis[doublon]
                        doublon -= 1
                    doublon += 1
                    compteurPB += 1
                    self.progressBar_01.setValue(compteurPB)
            except Exception:
                None

            doublon = 0
        # self.LA_Wait.setText("")
        self.progressBar_01.reset()
        self.progressBar_01.setStyleSheet("background-color: QPalette.Base")
        #### section nomenclature avec test sur volume ####

        ####title creation begin ###################################

        newSpreadSheetName = newSpreadSheetName
        ligne = 1
        colonne = 1

        try:
            tableau = FreeCAD.ActiveDocument.getObjectsByLabel(newSpreadSheetName)[
                0]  # for append in existant SpreadSheet
            ligne = decodeOccupation(tableau)[0] + 1
        except Exception:
            tableau = App.activeDocument().addObject('Spreadsheet::Sheet', newSpreadSheetName)  # for create SpreadSheet

        self.LE_SpreadSheet.setText(newSpreadSheetName)
        #       #[objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]

        objetdetail = ""  # variable for title

        if self.CB_01_Title.isChecked():  # Create title
            if self.CB_04_Name.isChecked():
                objetdetail = objetdetail + "Name object,"  # objName title

            if self.CB_05_Label.isChecked():
                objetdetail = objetdetail + "Label object,"  # objLabel title

            if self.CB_06_Nomenclature.isChecked():
                objetdetail = objetdetail + "Number,"  # Number title

            if self.CB_07_Solid.isChecked():
                objetdetail = objetdetail + "Type Solid,"  # objTypeSolid title

            if self.CB_08_Volume.isChecked():
                if self.CB_08_Split.isChecked():  # Volume title
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "Volume,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "Volume,v,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "Volume,v,v,"
                else:
                    objetdetail = objetdetail + "Volume,"

            if self.CB_09_Weight.isChecked():
                if self.CB_08_Split.isChecked():  # Weight title
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "Weight,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "Weight,w,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "Weight,w,w,"
                else:
                    objetdetail = objetdetail + "Weight,"

            if self.CB_10_Weight_Total.isChecked():
                if self.CB_08_Split.isChecked():  # Weight Total title
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "W_Total,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "W_Totalt,wt,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "W_Total,wt,wt,"
                else:
                    objetdetail = objetdetail + "W_Total,"

            if self.CB_11_Surface.isChecked():
                if self.CB_08_Split.isChecked():  # Surface title
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "Surface,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "Surface,s,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "Surface,s,s,"
                else:
                    objetdetail = objetdetail + "Surface,"

            if self.CB_12_BBox.isChecked():
                if self.CB_08_Split.isChecked():  # BBox title
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "BBox XL,BBox YL,BBox ZL,BBox Diag,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "BBox XL,b,BBox YL,b,BBox ZL,b,BBox Diag,b,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "BBox XL,b,b,BBox YL,b,b,BBox ZL,b,b,BBox Diag,b,b,"
                else:
                    objetdetail = objetdetail + "BBox XL,BBox YL,BBox ZL,BBox Diag,"

            if self.CB_13_Translate.isChecked():  # Translate title
                if self.CB_08_Split.isChecked():
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "Translate X,Translate Y,Translate Z,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "Translate X,t,Translate Y,t,Translate Z,t,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "Translate X,t,t,Translate Y,t,t,Translate Z,t,t,"
                else:
                    objetdetail = objetdetail + "Translate X,Translate Y,Translate Z,"

            if self.CB_14_Rotation.isChecked():  # Rotation  Yaw (Z) # Pitch (Y) # Roll (X) title
                if self.CB_08_Split.isChecked():
                    if self.RB_01_Value.isChecked():
                        objetdetail = objetdetail + "Rotation X,Rotation Y,Rotation Z,"
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + "Rotation X,r,Rotation Y,r,Rotation Z,r,"
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + "Rotation X,r,r,Rotation Y,r,r,Rotation Z,r,r,"
                else:
                    objetdetail = objetdetail + "Rotation X,Rotation Y,Rotation Z,"

            if self.CB_15_Dimension.isChecked():
                objetdetail = objetdetail + "Dimension ...,"  # Dimension title

            # options title color
            objetdetail = objetdetail[:len(objetdetail) - 1]
            objetdetail = objetdetail.split(",")

            if self.CB_01_Title.isChecked():  # Title
                for titleWrite in objetdetail:
                    titleWrite = titleWrite
                    tableau.setAlignment(caseTableau(ligne, colonne), str("center"))
                    tableau.setStyle(caseTableau(ligne, colonne), str("bold"))
                    if self.CB_02_Color.isChecked():  # Title color
                        tableau.setBackground(caseTableau(ligne, colonne),
                                              (TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                    tableau.set(caseTableau(ligne, colonne), str(titleWrite))
                    colonne += 1
        else:
            ligne -= 1

        ####title creation end ##################################

        objetdetail = unitSymbol = ""

        self.progressBar_01.setMaximum(len(listeSortedBis))
        compteurPB = 0

        ligne += 1
        for objListe in listeSortedBis:
            colonne = 1

            if self.CB_04_Name.isChecked():
                objetdetail = objListe[0]  # objName
                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                colonne += 1

            if self.CB_05_Label.isChecked():
                objetdetail = objListe[1]  # objLabel
                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                colonne += 1

            if self.CB_06_Nomenclature.isChecked():
                objetdetail = objListe[2]  # nomenclature
                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                colonne += 1

            if self.CB_07_Solid.isChecked():
                objetdetail = objListe[8]  # Solid
                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                colonne += 1

            if self.CB_08_Volume.isChecked():
                try:
                    volumeShape = FreeCAD.ActiveDocument.getObject(objListe[0]).Shape.Volume  # Volume
                    objetdetail = str(arround(volumeShape * uniteV))

                    if self.RB_01_Value.isChecked():
                        None  # 10.0
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + " " + uniteVs  # 10 mm^3
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + " " + uniteVs + " " + "Volume"  # 10 mm^3 Volume

                    tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                    tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                    if self.CB_08_Split.isChecked():
                        if self.CB_03_Colonne.isChecked():  # Title colonne color
                            tableau.setBackground(caseTableau(ligne, colonne),
                                                  (TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                        objectNumeric = objetdetail.split(" ")
                        for spl in objectNumeric:
                            objetdetail = spl
                            tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                            tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                        colonne -= 1
                    else:
                        try:
                            if self.RB_01_Value.isChecked():
                                None
                            else:
                                tableau.setDisplayUnit(caseTableau(ligne, colonne), uniteVs)
                        except Exception:
                            None
                        tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                except Exception:
                    None  # objetdetail = "."
                colonne += 1

            if self.CB_09_Weight.isChecked():  # poids
                try:
                    volumeShape = FreeCAD.ActiveDocument.getObject(objListe[0]).Shape.Volume  # Volume
                    objetdetail = str(arround(((volumeShape * densite) * uniteP) / 1000.0))

                    if self.RB_01_Value.isChecked():
                        None  # 10.0
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + " " + unitePs  # 10 kg
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + " " + unitePs + " " + "Weight"  # 10 kg Weight

                    tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                    tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                    if self.CB_08_Split.isChecked():
                        objectNumeric = objetdetail.split(" ")
                        if self.CB_03_Colonne.isChecked():  # Title colonne color
                            tableau.setBackground(caseTableau(ligne, colonne),
                                                  (TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                        for spl in objectNumeric:
                            objetdetail = spl
                            tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                            tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                        colonne -= 1
                    else:
                        try:
                            if self.RB_01_Value.isChecked():
                                None
                            else:
                                tableau.setDisplayUnit(caseTableau(ligne, colonne), unitePs)
                        except Exception:
                            None
                        tableau.set(caseTableau(ligne, colonne), str(objetdetail))

                except Exception:
                    None  # objetdetail = "."
                colonne += 1

            if self.CB_10_Weight_Total.isChecked():  # poids total
                try:
                    volumeShape = FreeCAD.ActiveDocument.getObject(objListe[0]).Shape.Volume  # Volume
                    objetdetail = str(arround(((volumeShape * densite) * uniteP) / 1000.0) * (float(objListe[2])))

                    if self.RB_01_Value.isChecked():
                        None  # 10.0
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + " " + unitePs  # 10 kg
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + " " + unitePs + " " + "W_Total"  # 10 kg W. Total

                    tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                    tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                    if self.CB_08_Split.isChecked():
                        objectNumeric = objetdetail.split(" ")
                        if self.CB_03_Colonne.isChecked():  # Title colonne color
                            tableau.setBackground(caseTableau(ligne, colonne),
                                                  (TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                        for spl in objectNumeric:
                            objetdetail = spl
                            tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                            tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                        colonne -= 1
                    else:
                        try:
                            if self.RB_01_Value.isChecked():
                                None
                            else:
                                tableau.setDisplayUnit(caseTableau(ligne, colonne), unitePs)
                        except Exception:
                            None
                        tableau.set(caseTableau(ligne, colonne), str(objetdetail))

                except Exception:
                    None  # objetdetail = "."
                colonne += 1

            if self.CB_11_Surface.isChecked():  # Surface
                try:
                    surfaceShape = FreeCAD.ActiveDocument.getObject(objListe[0]).Shape.Area  # Surface
                    objetdetail = str(arround(float(surfaceShape) * float(uniteS)))
                    if self.RB_01_Value.isChecked():
                        None  # 10.0
                    if self.RB_02_Val_Gr.isChecked():
                        objetdetail = objetdetail + " " + uniteSs  # 10 m2
                    if self.RB_03_Val_Gr_Ph.isChecked():
                        objetdetail = objetdetail + " " + uniteSs + " " + "Surface"  # 10 m2 Surface

                    tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                    tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                    if self.CB_08_Split.isChecked():
                        objectNumeric = objetdetail.split(" ")
                        if self.CB_03_Colonne.isChecked():  # Title colonne color
                            tableau.setBackground(caseTableau(ligne, colonne),
                                                  (TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                        for spl in objectNumeric:
                            objetdetail = spl
                            tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                            tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                        colonne -= 1
                    else:
                        try:
                            if self.RB_01_Value.isChecked():
                                None
                            else:
                                tableau.setDisplayUnit(caseTableau(ligne, colonne), uniteSs)
                        except Exception:
                            None
                        tableau.set(caseTableau(ligne, colonne), str(objetdetail))

                except Exception:
                    None  # objetdetail = "."
                colonne += 1

            if self.CB_12_BBox.isChecked():  # BoundBox
                try:
                    boundBoxShape = FreeCAD.ActiveDocument.getObject(objListe[0]).Shape.BoundBox
                    for i in range(4):
                        objetdetail = typeCoor = ""
                        if i == 0:
                            BoundBox = boundBoxShape.XLength  # Length x bBox
                            typeCoor = "X"
                        elif i == 1:
                            BoundBox = boundBoxShape.YLength  # Length y bBox
                            typeCoor = "Y"
                        elif i == 2:
                            BoundBox = boundBoxShape.ZLength  # Length z bBox
                            typeCoor = "Z"
                        elif i == 3:
                            BoundBox = boundBoxShape.DiagonalLength  # Diagonal bBox
                            typeCoor = "Diag"

                        objetdetail = str(arround(float(BoundBox) * uniteM))

                        if self.RB_01_Value.isChecked():
                            None  # 10.0
                        if self.RB_02_Val_Gr.isChecked():
                            objetdetail = objetdetail + " " + uniteMs  # 10 mm
                        if self.RB_03_Val_Gr_Ph.isChecked():
                            objetdetail = str(objetdetail) + " " + uniteMs + " BBox" + typeCoor  # 10 mm BoundBox

                        tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                        tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                        if self.CB_08_Split.isChecked():
                            objectNumeric = objetdetail.split(" ")
                            if self.CB_03_Colonne.isChecked():  # Title color
                                tableau.setBackground(caseTableau(ligne, colonne), (
                                TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                            for spl in objectNumeric:
                                objetdetail = spl
                                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                                colonne += 1
                        else:
                            try:
                                if self.RB_01_Value.isChecked():
                                    None
                                else:
                                    tableau.setDisplayUnit(caseTableau(ligne, colonne), uniteMs)
                            except Exception:
                                None
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                except Exception:
                    None

            if self.CB_13_Translate.isChecked():  # Placement_Translate
                try:
                    for i in range(3):
                        objetdetail = ""
                        basePlacement = FreeCAD.ActiveDocument.getObject(objListe[0]).Placement.Base[i]
                        objetdetail = str(arround(float(basePlacement) * uniteM))

                        if self.RB_01_Value.isChecked():
                            None  # 10.0
                        if self.RB_02_Val_Gr.isChecked():
                            objetdetail = objetdetail + " " + uniteMs  # 10 mm
                        if self.RB_03_Val_Gr_Ph.isChecked():
                            objetdetail = str(objetdetail) + " " + uniteMs + " T" + (chr(88 + i))  # 10 mm T

                        tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                        tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                        if self.CB_08_Split.isChecked():
                            objectNumeric = objetdetail.split(" ")
                            if self.CB_03_Colonne.isChecked():  # Title color
                                tableau.setBackground(caseTableau(ligne, colonne), (
                                TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                            for spl in objectNumeric:
                                objetdetail = spl
                                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                                colonne += 1
                        else:
                            try:
                                if self.RB_01_Value.isChecked():
                                    None
                                else:
                                    tableau.setDisplayUnit(caseTableau(ligne, colonne), uniteMs)
                            except Exception:
                                None
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                except Exception:
                    None

            if self.CB_14_Rotation.isChecked():  # Placement_Rotation Yaw (Z) # Pitch (Y) # Roll (X)
                try:
                    for i in range(3):
                        objetdetail = ""
                        rotationPlacement = FreeCAD.ActiveDocument.getObject(objListe[0]).Placement.Rotation.toEuler()[
                            i]
                        objetdetail = str(arround(float(rotationPlacement)))

                        try:
                            tableau.setDisplayUnit(caseTableau(ligne, colonne), "")
                        except Exception:
                            None
                        if self.RB_01_Value.isChecked():
                            None  # 10.0
                        if self.RB_02_Val_Gr.isChecked():
                            objetdetail = objetdetail + " " + "deg"  # 10 deg
                        if self.RB_03_Val_Gr_Ph.isChecked():
                            objetdetail = objetdetail + " " + "deg" + " R" + str((chr(88 + i)))  # 10 deg R

                        tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                        tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                        if self.CB_08_Split.isChecked():
                            objectNumeric = objetdetail.split(" ")
                            if self.CB_03_Colonne.isChecked():  # Title color
                                tableau.setBackground(caseTableau(ligne, colonne), (
                                TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                            for spl in objectNumeric:
                                objetdetail = spl
                                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                                tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                                colonne += 1
                        else:
                            tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                            colonne += 1
                except Exception:
                    None

            if self.CB_15_Dimension.isChecked():  # Dimension
                try:
                    objectNumeric = ""
                    obj = FreeCAD.ActiveDocument.getObject(objListe[0])
                    for modele in obj.PropertiesList:
                        if str(impost).find(str(modele)) != -1:
                            valeur = affDim(objListe[0], str(modele))
                            if valeur != 0.0:
                                objectNumeric = objetdetail = ""
                                objetdetail = str(valeur)

                                if grandeur == "mm":
                                    grandeur = uniteMs
                                    objetdetail = str(arround(float(valeur) * uniteM))
                                else:
                                    grandeur = grandeur

                                if self.RB_01_Value.isChecked():
                                    objectNumeric = objetdetail  # 0,0 = 10.0
                                if self.RB_02_Val_Gr.isChecked():
                                    objectNumeric = objetdetail + " " + grandeur  # 1,0 = 10 mm
                                if self.RB_03_Val_Gr_Ph.isChecked():
                                    objectNumeric = objetdetail + " " + grandeur + " " + modele  # 1,1 = 10 mm Width

                                tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                                tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))

                                if self.CB_08_Split.isChecked():
                                    objectNumeric = objectNumeric.split(" ")
                                    if self.CB_03_Colonne.isChecked():  # Title color
                                        tableau.setBackground(caseTableau(ligne, colonne), (
                                        TextColorText_R, TextColorText_G, TextColorText_B, TextColorText_L))
                                    for spl in objectNumeric:
                                        objetdetail = spl
                                        tableau.setAlignment(caseTableau(ligne, colonne), str("right"))
                                        tableau.setAlignment(caseTableau(ligne, colonne), str("vcenter"))
                                        tableau.set(caseTableau(ligne, colonne), str(objetdetail))
                                        colonne += 1
                                else:
                                    objectNumeric = str(objectNumeric)
                                    try:
                                        if self.RB_01_Value.isChecked():
                                            None
                                        else:
                                            tableau.setDisplayUnit(caseTableau(ligne, colonne), grandeur)
                                    except Exception:
                                        None
                                    tableau.set(caseTableau(ligne, colonne), (objectNumeric))
                                    colonne += 1
                except Exception:
                    None

            ligne += 1
            compteurPB += 1
            self.progressBar_01.setValue(compteurPB)

        self.progressBar_01.setValue(0)

        ui.on_PB_SpreadSheet_clicked()
        del listeSortedBis[:]
        App.ActiveDocument.recompute()

    ########SpreadSheet section fin #######################################################################################################

    def loadObjects(self):
        global doc
        global listeObjetsOriginal
        global listeSorted
        global ui
        global titre
        global impost

        enteteTitres = QtWidgets.QTreeWidgetItem(["Etiquette", ])  # titres entete 1 colonnes
        self.treeWidget.setHeaderItem(enteteTitres)  # affichage des titres #(["Tree","First",...])
        documentActif = QtWidgets.QTreeWidgetItem(self.treeWidget, [str(doc) + " Original"])  # titre du document

        del listeObjetsOriginal[:]
        del listeSorted[:]

        listeType = []
        del listeType[:]

        c = 0
        #### Liste ######
        for obj in FreeCAD.ActiveDocument.Objects:
            objName = obj.Name
            objLabel = obj.Label
            objGroupe = ""
            objLName = 0
            objLLabel = 0
            objLGroupe = 0
            objSignal = 0

            if objLabel[0].islower():  # firt char lower
                objLabel = objLabel[0].upper() + objLabel[1:]
                objSignal = 1

            ####recherche de groupe et enfants debut####
            if len(obj.OutList) != 0:
                if len(obj.OutList) > 1:
                    objGroupe = obj.Label + " (" + str(len(obj.OutList)) + " Objects)"
                else:
                    objGroupe = obj.Label + " (" + str(len(obj.OutList)) + " Object)"
                for enfants in obj.OutList:
                    objGroupe += "\n" + " ( " + enfants.Label + " )"
            else:
                objGroupe = "-"
            ####recherche de groupe et enfants fin####

            #       #[objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]

            ####recherche de type d objet debut####
            objTypeSolid = objTypeTypeID = objTypeShape = ""
            try:
                if str(obj.Shape.Solids).find('Solid') != -1:
                    objTypeSolid = "Solid"
                    listeType.append("Solid")
            except Exception:
                None
            try:
                listeType.append(str(obj.TypeId.split("::")[1]))
                objTypeTypeID = str(obj.TypeId.split("::")[1])
            except Exception:
                None
            try:
                listeType.append(str(obj.Shape.ShapeType))
                objTypeShape = str(obj.Shape.ShapeType)
            except Exception:
                None
            ####recherche de type d objet fin####

            objLName = len(objName)  # length
            objLLabel = len(objLabel)  # length
            objLGroupe = len(objGroupe)  # length

            ####recherche de type numerique debut####
            objNumeric = ""
            for i in obj.PropertiesList:
                if str(impost).find(str(i)) != -1:
                    if (affDim(obj.Name, str(i))) != 0.0:
                        objNumeric = objNumeric + str(int(affDim(obj.Name, str(i)))) + ","  # int numeric
            ####recherche de type numerique fin####

            ####
            #            if Gui.activeDocument().getObject(objName).Visibility == True:
            #                listeObjetsOriginal.append([objName, objLabel, "True", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]])
            #            else:
            #                listeObjetsOriginal.append([objName, objLabel, "False", objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]])
            listeObjetsOriginal.append(
                [objName, objLabel, str(Gui.activeDocument().getObject(objName).Visibility), objGroupe, objLName,
                 objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]])
        ####
        ####
        self.treeWidget.clear()  # efface le contenu du widget
        listeSorted = copy.deepcopy(listeObjetsOriginal)  # original organisation on begin
        titre = " Original"  # original organisation on begin
        #
        #        listeSorted = sorted(listeSorted, key=itemgetter(0))                        # sorted by Name on begin
        #        titre = " by Name"                                                          # sorted by Name on begin
        ####
        ####
        listeType = sorted(set(listeType))  # supprime les doublons et met en ordre liste Type
        for i in range(len(listeType)):
            self.ComboB_Type.addItem(_fromUtf8(""))  # include in ComboBox
            self.ComboB_Type.setItemText(i, listeType[i])
        ####
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    #        ui.tableauSpreadsheet()

    def on_PB_Visibility_clicked(self):
        global visibilite
        global group
        global ui
        global listeSorted

        group = 0
        if visibilite == 0:
            visibilite = 1
        else:
            visibilite = 0

        visible = cache = 0
        for i in listeSorted:
            if i[2] == "True":
                visible += 1
            else:
                cache += 1
        self.treeWidget.clear()  # efface le widget
        ui.sorted_List(titre + " (V " + str(visible) + ") (H " + str(cache) + ") = (O " + str(visible + cache) + ")")

    def on_PB_Group_clicked(self):
        global group
        global visibilite
        global ui
        global listeSorted

        visibilite = 0
        if group == 0:
            group = 1
        else:
            group = 0

        groupe = simple = 0
        for i in listeSorted:
            if i[3] == "-":
                groupe += 1
            else:
                simple += 1

        self.treeWidget.clear()  # efface le widget
        ui.sorted_List(titre + " (G " + str(groupe) + ") (S " + str(simple) + ") = (O " + str(groupe + simple) + ")")

    def on_PB_Original_clicked(self):  # tableau organisation
        global listeObjetsOriginal
        global listeSorted
        global ui
        global titre

        self.lineEdit_Search.clear()
        for obj in listeObjetsOriginal:
            if obj[2] == "True":
                Gui.activeDocument().getObject(obj[0]).Visibility = True
            else:
                Gui.activeDocument().getObject(obj[0]).Visibility = False

        listeSorted = copy.deepcopy(listeObjetsOriginal)
        self.treeWidget.clear()
        titre = " Original"
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")
        self.treeWidget.verticalScrollBar().setStyleSheet("background-color: QPalette.Base;")

    def on_PB_All_Visible_clicked(self):
        global listeSorted
        global ui
        global titre

        i = 0
        for obj in listeSorted:
            Gui.activeDocument().getObject(obj[0]).Visibility = True
            listeSorted[i][2] = "True"
            i += 1
        self.treeWidget.clear()  # efface le widget
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    def on_PB_All_Hidden_clicked(self):
        global listeSorted
        global ui
        global titre

        i = 0
        for obj in listeSorted:
            Gui.activeDocument().getObject(obj[0]).Visibility = False
            listeSorted[i][2] = "False"
            i += 1
        self.treeWidget.clear()  # efface le widget
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    def on_PB_Reload_clicked(self):
        global doc
        global ui
        global titre

        self.PB_SpreadSheet.setStyleSheet("background-color: QPalette.Base")
        doc = App.activeDocument()
        if doc == None:
            doc = FreeCAD.newDocument()
        doc = doc.Name  # unicode(doc.Name)

        self.lineEdit_Search.clear()
        self.treeWidget.clear()
        self.RB_01_NameLabel.setChecked(True)  #
        titre = " Original"
        ui.loadObjects()

    def on_RB_Pressed(self):
        global ui
        global titre

        self.treeWidget.clear()
        ui.on_lineEdit_Search_Pressed()

    def on_lineEdit_Search_Pressed(self):
        global ui
        global titre
        global listeSorted
        global searchString
        global listeObjetsOriginal
        global listeByStringSear

        self.treeWidget.clear()
        titre = " by string"
        texte = self.lineEdit_Search.text()
        searchString = " Searched"
        listeSorted = copy.deepcopy(listeObjetsOriginal)
        del listeByStringSear[:]

        if texte != "":
            comptName = comptLabel = comptNumeric = 0

            # Search by Name + Label (not casse)
            if self.RB_01_NameLabel.isChecked():
                texte = texte.upper()
                for i in range(len(listeSorted)):
                    if texte in listeSorted[i][0][:len(texte)].upper():  # Name  upper
                        listeByStringSear.append(listeSorted[i])
                        comptName += 1
                    if texte in listeSorted[i][1][:len(texte)].upper():  # Label upper
                        listeByStringSear.append(listeSorted[i])
                        comptLabel += 1

            # Search by Name (casse)
            elif self.RB_02_Name_CS.isChecked():  # case sensitivity
                for i in range(len(listeSorted)):
                    if texte in listeSorted[i][0][:len(texte)]:  # Name
                        listeByStringSear.append(listeSorted[i])
                        comptName += 1

            # Search by Label (not casse)
            elif self.RB_03_Label_NC.isChecked():
                for i in range(len(listeSorted)):
                    if texte.upper() in listeSorted[i][1][:len(texte)].upper():  # Label
                        listeByStringSear.append(listeSorted[i])
                        comptLabel += 1

            # Search by Name + Label casse sensitivity
            elif self.RB_04_NamLabel_CS.isChecked():
                for i in range(len(listeSorted)):
                    if texte in listeSorted[i][0][:len(texte)]:  # Name  sensitivity
                        listeByStringSear.append(listeSorted[i])
                        comptName += 1
                    if listeSorted[i][7] == 1:
                        casse = listeSorted[i][1]
                        casse = casse[0].lower() + casse[1:]
                        if texte in casse[:len(texte)]:  # Label sensitivity
                            listeByStringSear.append(listeSorted[i])
                            comptLabel += 1
                    elif texte in listeSorted[i][1][:len(texte)]:  # Label sensitivity
                        listeByStringSear.append(listeSorted[i])
                        comptLabel += 1

            # Search by case sensitivity in word
            elif self.RB_05_NameLabel_AL.isChecked():
                for i in range(len(listeSorted)):
                    if texte in listeSorted[i][0]:  # Name sensitivity in word
                        listeByStringSear.append(listeSorted[i])
                        comptName += 1
                    if listeSorted[i][7] == 1:
                        casse = listeSorted[i][1]
                        casse = casse[0].lower() + casse[1:]
                        if texte in casse:  # Label sensitivity in word
                            listeByStringSear.append(listeSorted[i])
                            comptLabel += 1
                    elif texte in listeSorted[i][1]:  # Label sensitivity in word
                        listeByStringSear.append(listeSorted[i])
                        comptLabel += 1

            titre = " by string"

            # Search by Numeric value
            if self.RB_06_Numeric_Num.isChecked():
                titre = " by numeric"
                for i in range(len(listeSorted)):
                    decoNumer = listeSorted[i][11][0].split(",")
                    if texte in decoNumer:  # Numeric
                        listeByStringSear.append(listeSorted[i])
                        comptNumeric += 1
            listeSorted = copy.deepcopy(listeByStringSear)

            ui.sorted_List(titre + " (N " + str(comptName) + ") (L " + str(comptLabel) + ") (Nu " + str(
                comptNumeric) + ") = (T " + str(comptName + comptLabel + comptNumeric) + ")")
        else:
            listeSorted = copy.deepcopy(listeObjetsOriginal)
            ui.on_PB_ClearLEdit_clicked()

    def on_PB_ClearLEdit_clicked(self):
        global ui
        global titre
        global searchString

        searchString = ""
        self.treeWidget.clear()
        self.lineEdit_Search.clear()
        # self.RB_01_NameLabel.setChecked(True)
        titre = " Original"
        ui.sorted_List(titre + " (O " + str(len(listeSorted)) + ")")

    def on_PB_Select_clicked(self):
        global listeSorted
        global ui
        global titre
        global selections

        self.treeWidget.setToolTip("The title display the option, number and type object(s) displayed" + "\n" + "\n" +
                                   "O = Objects" + "\n" +
                                   "N = Name" + "\n" +
                                   "L = Label" + "\n" +
                                   "T = Total" + "\n" +
                                   "G = Group" + "\n" +
                                   "S = Single" + "\n" +
                                   "V = Visible" + "\n" +
                                   "H = Hidden" + "\n\n" +
                                   "If one object are selected :" + "\n" +
                                   "the Placement Base, Rotation and Center of mass is displayed" + "\n" +
                                   "if available !")
        if selections == 0:
            self.PB_Select.setText("Deselect")
            self.PB_Select.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_24.png"))
            self.PB_Select.setToolTip(
                "Deselect all object(s) selected <img src=" + self.path + "Macro_FCTreeView_24.png" + " />")
            self.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
            self.treeWidget.selectAll()
            for obj in listeSorted:
                FreeCADGui.Selection.addSelection(App.ActiveDocument.getObject(obj[0]))
                # FreeCADGui.Selection.addSelection(App.ActiveDocument.getObject(unicode(obj[0])))
            selections = 1
        else:
            self.PB_Select.setText("Select")
            self.PB_Select.setIcon(QtGui.QIcon(self.path + "Macro_FCTreeView_23.png"))
            self.PB_Select.setToolTip(
                "Select all object(s) displayed <img src=" + self.path + "Macro_FCTreeView_23.png" + " />")
            self.treeWidget.clearSelection()
            FreeCADGui.Selection.clearSelection()
            selections = 0

    def SIGNAL_ComboB_Type_Changed(self, item):
        global ui
        global titre
        global listeSorted
        global searchString
        global listeObjetsOriginal
        global listeByStringSear

        self.lineEdit_Search.clear()
        texte = self.ComboB_Type.itemText(item)
        self.treeWidget.clear()
        titre = " by type object"
        searchString = " Searched"
        listeSorted = copy.deepcopy(listeObjetsOriginal)

        del listeByStringSear[:]
        #       [objName, objLabel, str(Gui.activeDocument().getObject(objName).Visibility), objGroupe, objLName, objLLabel, objLGroupe, objSignal, objTypeSolid, objTypeTypeID, objTypeShape, [objNumeric]]
        if texte != "":
            comp = 0
            # Search by type object
            for i in range(len(listeSorted)):
                if (texte in listeSorted[i][8]) or (texte in listeSorted[i][9]) or (texte in listeSorted[i][10]):
                    listeByStringSear.append(listeSorted[i])
                    comp += 1
            titre = " by " + texte
            listeSorted = copy.deepcopy(listeByStringSear)
            ui.sorted_List(titre + " ( " + texte + " " + str(comp) + ")")
        else:
            listeSorted = copy.deepcopy(listeObjetsOriginal)
            ui.on_PB_ClearLEdit_clicked()

    def on_PB_Quit_clicked(self):
        global ui
        #        self.vueActive.removeEventCallback("SoMouseButtonEvent",self.click)         # desinstalle la fonction souris
        FreeCADGui.Selection.removeObserver(s)  # desinstalle la fonction residente SelObserver
        self.window.hide()  # hide the window and close the macro

        FreeCAD.Console.PrintMessage("Quit FCTreeView" + "\n")


##################################################################################################
class SelObserver:
    def addSelection(self, document, object, element, position):  # Selection
        global sourisPass
        global listeSorted
        global ui

        None


#
#        if sourisPass == 0:
#            if object in listeSorted[0]:
#                print "wahou"
#                print object
#            sourisPass = 1
#        else:
#            sourisPass = 0
#
#
##        print object
#
###    def setPreselection(self,doc,obj,sub):             # preselection
###        print "setPreselection"
###    def removeSelection(self,doc,obj,sub):             # Effacer l'objet selectionne
###        print "removeSelection"
###    def setSelection(self,doc):                        # Selection dans ComboView
###        print "SelObserver quit macro"
###    def clearSelection(self,doc):                      # Si clic sur l'ecran, effacer la selection
###        print "clearSelection"                         # Si clic sur un autre objet, efface le precedent
#
s = SelObserver()
FreeCADGui.Selection.addObserver(s)  # installe la fonction en mode resident
####################################################################################################

doc = App.activeDocument()
if doc == None:
    doc = FreeCAD.newDocument()
doc = doc.Name

#####Section demarrage et controle#################################################################
#
mw = FreeCADGui.getMainWindow()
dw = mw.findChildren(QtWidgets.QDockWidget)  # pour QtWidgets Docked et pas les Flotants

for i in dw:
    if str(i.objectName()) == __title__:
        FreeCAD.Console.PrintError(__title__ + " is already open see \"Menu > View > Panels\"" + "\n")
        # va=i.toggleViewAction()
        if i.isVisible():
            # va.setChecked(False)                   # activer False
            i.setVisible(False)  # visible False
        else:
            # va.setChecked(True)                    # activer True
            i.setVisible(True)  # visible True
        break

if i.objectName() != __title__:  # macro Name
    if testing == 1:  # MainWindow
        MainWindow = QtWidgets.QMainWindow()  # create a new window volant
        MainWindow.setObjectName(__title__)  # macro internal Name
        ui = Ui_MainWindow(MainWindow)
        ui.setupUi(MainWindow)
        MainWindow.show()
        # ui.loadObjects()
        ui.on_PB_Reload_clicked()  # load and run the macro

    #
    #####DockWidget################################################################################
    #
    else:
        MainWindow = QtWidgets.QDockWidget()  # create a new dockwidget
        MainWindow.setObjectName(__title__)
        ui = Ui_MainWindow(MainWindow)
        ui.setupUi(MainWindow)
        FCmw = FreeCADGui.getMainWindow()

        if testing == 2:  # RightDock
            FCmw.addDockWidget(PySide2.QtCore.Qt.RightDockWidgetArea,
                               MainWindow)  # add the widget to the main window Right
        else:  # LeftDock
            FCmw.addDockWidget(PySide2.QtCore.Qt.LeftDockWidgetArea,
                               MainWindow)  # add the widget to the main window Left
        # ui.loadObjects()
        ui.on_PB_Reload_clicked()  # load and run the macro


