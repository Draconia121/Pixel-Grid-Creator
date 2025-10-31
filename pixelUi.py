
from PySide2 import QtWidgets, QtCore, QtGui
import maya.OpenMayaUI as omui
import shiboken2
from functools import partial

import maya.cmds as cmds

class SimpleColorPicker(QtWidgets.QDialog):
    color_selected = QtCore.Signal(QtGui.QColor)
    def __init__(self, parent=None):
        super(SimpleColorPicker, self).__init__(parent)
        self.setWindowTitle("Color Palette")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.colors = ['#ff4d4d', '#ff944d', '#ffff4d', '#94ff4d', '#4dff4d', '#4dff94', '#4dffff', '#4d94ff', '#4d4dff', '#944dff', '#ff4dff', '#ff4d94', '#ffffff', '#c0c0c0', '#808080', '#000000']
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(2)
        columns = 4
        for i, hex_color in enumerate(self.colors):
            color = QtGui.QColor(hex_color)
            button = QtWidgets.QPushButton()
            button.setFixedSize(40, 40)
            button.setStyleSheet("background-color: {}; border: 1px solid #222;".format(hex_color))
            button.clicked.connect(partial(self.on_color_button_clicked, color))
            row, col = i // columns, i % columns
            self.main_layout.addWidget(button, row, col)
    def on_color_button_clicked(self, color):
        self.color_selected.emit(color)
    def closeEvent(self, event):
        self.hide()
        event.ignore()

def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class PixelGridCreatorWindow(QtWidgets.QDialog):
    ui_instance = None
    @staticmethod
    def show_dialog():
        if not PixelGridCreatorWindow.ui_instance:
            PixelGridCreatorWindow.ui_instance = PixelGridCreatorWindow()
        if PixelGridCreatorWindow.ui_instance.isHidden():
            PixelGridCreatorWindow.ui_instance.show()
        else:
            PixelGridCreatorWindow.ui_instance.raise_()
            PixelGridCreatorWindow.ui_instance.activateWindow()

    def __init__(self, parent=get_maya_main_window()):
        super(PixelGridCreatorWindow, self).__init__(parent)
        self.setWindowTitle("Move Tool Pixel (PySide)")
        self.setObjectName("PixelGridCreatorPySideWindow")
        self.setMinimumSize(440, 520)
        self.setStyleSheet(
            '''
                QDialog {
                    background-color: #48756d; 
                    font-family: Arial, sans-serif; 
            }
                QPushButton {
                    background-color: #1b3833;
                    color: #f0f0f0;
                    border: 1px solid #222222;
                    border-radius: 4px;         
                    padding: 5px;
                    font-weight: bold;
            }
            '''
            )
            
        self.grid_size = 10
        self.created_cubes = []
        self.color_picker = None
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

            
    def create_widgets(self):
        self.grid_buttons = []
        for i in range(self.grid_size * self.grid_size):
            button = QtWidgets.QPushButton()
            button.setFixedSize(40, 40)
            button.setStyleSheet("background-color: #444;")
            self.grid_buttons.append(button)
        self.separator = QtWidgets.QFrame()
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.color_btn = QtWidgets.QPushButton("Change Color")
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.reset_btn = QtWidgets.QPushButton("Reset All")

    def create_layouts(self):
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setSpacing(2)
        for i, button in enumerate(self.grid_buttons):
            row, col = i // self.grid_size, i % self.grid_size
            self.grid_layout.addWidget(button, row, col)
        self.control_layout = QtWidgets.QHBoxLayout()
        self.control_layout.addWidget(self.color_btn)
        self.control_layout.addWidget(self.delete_btn)
        self.control_layout.addWidget(self.reset_btn)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addWidget(self.separator)
        self.main_layout.addLayout(self.control_layout)

    def create_connections(self):
        for i, button in enumerate(self.grid_buttons):
            row, col = i // self.grid_size, i % self.grid_size
            button.clicked.connect(partial(self.on_grid_cell_click, row, col))
        self.color_btn.clicked.connect(self.on_color_click)
        self.delete_btn.clicked.connect(self.on_delete_click)
        self.reset_btn.clicked.connect(self.on_reset_click)

    def on_grid_cell_click(self, row, col):
        cube_name = "pixel_cube_{}_{}".format(row, col)
        if not cmds.objExists(cube_name):
            new_cube = cmds.polyCube(name=cube_name, width=1, height=1, depth=1)[0]
            cmds.move(col, 0.5, row, new_cube)
            cmds.makeIdentity(new_cube, apply=True, t=1, r=1, s=1, n=0)
            self.created_cubes.append(new_cube)
            button_index = row * self.grid_size + col
            self.grid_buttons[button_index].setStyleSheet("background-color: #5599ff;")
        else:
            cmds.select(cube_name, replace=True)

    def on_color_click(self):
        if not self.color_picker:
            self.color_picker = SimpleColorPicker(parent=self)
            self.color_picker.color_selected.connect(self.apply_color_to_selection)
        if self.color_picker.isHidden():
            self.color_picker.show()
        else:
            self.color_picker.raise_()
            self.color_picker.activateWindow()


    def apply_color_to_selection(self, q_color):
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning("Please select a pixel cube to color.")
            return

        rgb_values = [q_color.redF(), q_color.greenF(), q_color.blueF()]
        style_sheet = "background-color: {};".format(q_color.name())
        
        for obj in selection:
            new_shader = cmds.shadingNode('standardSurface', asShader=True, name=obj + '_shader#')
            cmds.setAttr(new_shader + '.baseColor', rgb_values[0], rgb_values[1], rgb_values[2], type='double3')
            cmds.setAttr(new_shader + '.specular', 0.1)
            new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=obj + '_sg#')
            cmds.connectAttr(new_shader + '.outColor', new_sg + '.surfaceShader')
            cmds.sets(obj, edit=True, forceElement=new_sg)

            if obj in self.created_cubes:
                try:
                    parts = obj.split('_')
                    row, col = int(parts[2]), int(parts[3])
                    button_index = row * self.grid_size + col
                    self.grid_buttons[button_index].setStyleSheet(style_sheet)
                except (IndexError, ValueError): pass
        
        cmds.select(clear=True)

    def on_delete_click(self):
        selection = cmds.ls(selection=True)
        if not selection: return
        for obj in selection:
            if obj in self.created_cubes:
                try:
                    parts = obj.split('_')
                    row, col = int(parts[2]), int(parts[3])
                    button_index = row * self.grid_size + col
                    self.grid_buttons[button_index].setStyleSheet("background-color: #444;")
                except (IndexError, ValueError): pass
                self.created_cubes.remove(obj)
        cmds.delete(selection)
        
    def on_reset_click(self):
        confirm = QtWidgets.QMessageBox.question(self, 'Confirm Reset', 'Are you sure?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if confirm == QtWidgets.QMessageBox.Yes:
            existing = [c for c in self.created_cubes if cmds.objExists(c)]
            if existing: cmds.delete(existing)
            self.created_cubes = []
            for btn in self.grid_buttons: btn.setStyleSheet("background-color: #444;")

    def closeEvent(self, event):
        if self.color_picker:
            self.color_picker.deleteLater()
        super(PixelGridCreatorWindow, self).closeEvent(event)
        PixelGridCreatorWindow.ui_instance = None


try:
    pixel_grid_creator_dialog.close()
    pixel_grid_creator_dialog.deleteLater()
except NameError:
    pass

pixel_grid_creator_dialog = PixelGridCreatorWindow()
pixel_grid_creator_dialog.show()
