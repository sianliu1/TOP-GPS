import json
import os.path
import sys
import subprocess
import shutil
import tempfile
import vtk
import numpy as np
from scipy.spatial import cKDTree
from PySide6.QtCore import Qt, QEvent, QTime, QThread
from PySide6.QtWidgets import QApplication, QMainWindow, QSlider, QVBoxLayout, QLabel, QFileDialog, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QMessageBox, QDialog, QWidget, QPushButton, QProgressDialog
from PySide6.QtUiTools import QUiLoader
from mainwindow_ui import Ui_MainWindow
import SimpleITK as sitk  # 用于读取nii.gz数据
from interactormethod import  update_slice
from basewindow import SliceWin, ThreeDimWin,SliceWin2,SliceWin3
from vtkmodules.util import numpy_support as nps

import nibabel as nib  # 用于读取nii.gz数据
from reconstruction import rec_all,MeshProcess,RecData,DataInfo
from secret_manage import decrypted_secret_key

#预览图像函数
from dcm_reader import PreviewWindow,DicomLoader

import pydicom
from PySide6.QtGui import QColor




class ModelItemWidget(QWidget):
    def __init__(self, name:str, actor:vtk.vtkActor, color_rgb, parent=None, on_focus=None, on_highlight=None, on_unhighlight=None):
        super().__init__(parent)
        self.actor = actor
        self.name = name
        self.on_focus = on_focus
        self.on_highlight = on_highlight
        self.on_unhighlight = on_unhighlight
        # Normalize color to 0-255
        if isinstance(color_rgb, (list, tuple)) and len(color_rgb) >= 3:
            if max(color_rgb) <= 1.0:
                r,g,b = [int(max(0,min(1,c))*255) for c in color_rgb[:3]]
            else:
                r,g,b = [int(max(0,min(255,c))) for c in color_rgb[:3]]
        else:
            r,g,b = 200,200,200
        self.base_color = QColor(r,g,b)
        # UI
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_Hover, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8,4,8,4)
        layout.setSpacing(8)
        # Color swatch
        self.swatch = QLabel()
        self.swatch.setFixedSize(18,18)
        self.swatch.setStyleSheet(f"border-radius:3px; background-color: rgb({r},{g},{b}); border:1px solid rgba(255,255,255,80);")
        # Eye toggle — manual state, no setCheckable to avoid hover pseudo-state bugs
        self._visible = True
        self.btn_eye = QPushButton("👁")
        self.btn_eye.setFixedWidth(28)
        self.btn_eye.setFocusPolicy(Qt.NoFocus)
        self._eye_style_visible = "QPushButton{background:transparent; color:white; border:none;}"
        self._eye_style_hidden  = "QPushButton{background:transparent; color:gray; border:none;}"
        self.btn_eye.setStyleSheet(self._eye_style_visible)
        self.btn_eye.clicked.connect(self._on_eye_clicked)
        # Name
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("color:black;")
        # Spacer
        spacer = QSpacerItem(10,10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setValue(100)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.setFixedHeight(20)
        self.slider.setMinimumWidth(200)  # widen slider
        self.slider.valueChanged.connect(self._on_opacity_changed)
        self.slider.setToolTip("Opacity")
        slider_style = f"""
            QSlider::groove:horizontal {{ height:8px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 rgba({r},{g},{b},190), stop:1 rgba({r},{g},{b},90)); border-radius:4px; }}
            QSlider::handle:horizontal {{ background: rgba({r},{g},{b},255); width:14px; height:14px; margin:-5px 0;
                border:2px solid rgba(255,255,255,170); border-radius:7px; }}
            QSlider::handle:horizontal:hover {{ border:2px solid black; }}
            QSlider::handle:horizontal:pressed {{ background: rgba({r},{g},{b},230); }}
            QSlider::sub-page:horizontal {{ background: rgba({r},{g},{b},140); border-radius:4px; }}
            QSlider::add-page:horizontal {{ background: rgba(40,40,40,80); border-radius:4px; }}
        """
        self.slider.setStyleSheet(slider_style)
        self.lbl_val = QLabel("100%")
        self.lbl_val.setStyleSheet("color:rgba(255,255,255,180);")
        layout.addWidget(self.swatch)
        layout.addWidget(self.btn_eye)
        layout.addWidget(self.lbl_name)
        layout.addItem(spacer)
        layout.addWidget(self.slider)
        layout.addWidget(self.lbl_val)
        self.setLayout(layout)
        self._hovered = False
        self._edges_prev = 0
        self._line_width_prev = 1

    def set_visibility(self, vis: bool):
        """Programmatically set visibility (updates both actor and UI)."""
        self._visible = vis
        self._apply_visibility()

    def _on_eye_clicked(self):
        """Handle eye button click — toggle state and apply immediately."""
        self._visible = not self._visible
        self._apply_visibility()

    def _apply_visibility(self):
        vis = self._visible
        # Update button style immediately
        self.btn_eye.setStyleSheet(self._eye_style_visible if vis else self._eye_style_hidden)
        self.btn_eye.setText("👁" if vis else "🚫")
        self.actor.SetVisibility(vis)
        if not vis:
            if self.on_unhighlight:
                self.on_unhighlight(self.actor)
            try:
                self.actor.GetProperty().SetEdgeVisibility(0)
            except Exception:
                pass
        self.slider.setEnabled(vis)
        self.lbl_name.setEnabled(vis)
        self.lbl_val.setEnabled(vis)
        top = self._find_model_win()
        if top: top.win.Render()

    def _on_opacity_changed(self, val:int):
        self.actor.GetProperty().SetOpacity(val/100.0)
        self.lbl_val.setText(f"{val}%")
        rgba = f"rgba({self.base_color.red()},{self.base_color.green()},{self.base_color.blue()},{60+int(val*0.4)})"
        self.swatch.setStyleSheet(f"border-radius:3px; background-color: {rgba}; border:1px solid rgba(255,255,255,80);")
        top = self._find_model_win()
        if top: top.win.Render()

    def _find_model_win(self):
        # climb up to find ThreeDimWin wrapper
        p = self.parent()
        depth = 0
        while p is not None and depth < 6:
            if hasattr(p, 'win') and isinstance(getattr(p,'win'), vtk.vtkRenderWindow):
                return p
            p = p.parent()
            depth += 1
        return None

    def enterEvent(self, e):
        super().enterEvent(e)
        if self.on_highlight:
            self.on_highlight(self.actor)
        # background highlight
        self.setStyleSheet("background-color: rgba(255,255,255,20); border-radius:6px;")

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self.on_unhighlight:
            self.on_unhighlight(self.actor)
        self.setStyleSheet("")

    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        if self.on_focus:
            self.on_focus(self.actor)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.secret_config()

        self.axial_slider = self.ui.Bar1
        self.coronal_slider = self.ui.Bar2
        self.sagittal_slider = self.ui.Bar3


        self.actors = []
        self.type = "lungsystem"
        self.info = DataInfo()
        self.ct_itk = None
        self.label_np = None
        self.rec_datas = []

        self.dicom_path = None
        self.patient_name = None
        self.single_view_active = False
        self.single_view_widget = None

        # 创建vtk渲染窗口
        self.slice_wins = [SliceWin3(self.ui.win1,win_type="axial"), SliceWin3(self.ui.win2,win_type="coronal"), SliceWin3(self.ui.win3,win_type="sagittal")]


        tmp_ui_wins = [self.ui.win1, self.ui.win2, self.ui.win3]
        for tmp_win,tmp_ui in zip(self.slice_wins,tmp_ui_wins):
            tmp_layout = QVBoxLayout(tmp_ui)
            tmp_layout.addWidget(tmp_win)

        self.model_win = ThreeDimWin(self.ui.win4)
        tmp_layout = QVBoxLayout(self.ui.win4)
        tmp_layout.addWidget(self.model_win)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { background-color: rgba(0,0,0,120); color: white; padding:4px; font: 12px 'Microsoft YaHei'; }")
        self.info_label.setAlignment(Qt.AlignCenter)
        # Rebuild win4 layout to put label on top
        if self.ui.win4.layout():
            lay = self.ui.win4.layout()
            lay.insertWidget(0, self.info_label)
        else:
            lay = QVBoxLayout(self.ui.win4)
            lay.addWidget(self.info_label)
            lay.addWidget(self.model_win)

        self.slice_win_left_press = False
        self.slice_win_left_release = True
        self.slice_win_right_press = False
        self.slice_win_right_release = True

        #读取配置
        self.config = None
        with open('config.json', 'r') as f:
            self.config = json.load(f)

        if self.config is None:
            raise ValueError("config.json is not found or is empty")




        # 设置滑块信号槽
        self.axial_slider.valueChanged.connect(self.update_axial_slice)
        self.coronal_slider.valueChanged.connect(self.update_coronal_slice)
        self.sagittal_slider.valueChanged.connect(self.update_sagittal_slice)

        self.ui.btn_input_data.clicked.connect(self.open_file)
        self.ui.btn_autorec.clicked.connect(self.auto_rec_all)
        self.ui.btn_watershed.clicked.connect(self.watershed_analysis)

        #设置滚轮事件
        self.slice_wins[0].signal_wheel.connect(lambda val:self._slot_wheel(self.axial_slider,val))
        self.slice_wins[1].signal_wheel.connect(lambda val:self._slot_wheel(self.coronal_slider,val))
        self.slice_wins[2].signal_wheel.connect(lambda val:self._slot_wheel(self.sagittal_slider,val))

        #窗宽窗位
        self.ui.actionlung.triggered.connect(lambda:self.change_win_level("lung"))
        self.ui.actionbone.triggered.connect(lambda:self.change_win_level("bone"))
        self.ui.actionliver.triggered.connect(lambda:self.change_win_level("liver"))
        self.ui.actionbrain.triggered.connect(lambda:self.change_win_level("brain"))

        #导出stl
        self.ui.actionstl.triggered.connect(self.export_stl)
        # self.installEventFilter(self)

        for tmp_win in self.slice_wins:
            tmp_win.installEventFilter(self)
        self.model_win.installEventFilter(self)

        self.model_item_widgets = []  # initialize list for model item widgets
        self._is_closing = False
        # Widen label panel so sliders can be longer
        try:
            self.ui.label_menu.setMinimumWidth(300)
        except Exception:
            try:
                self.ui.label_plate.setMinimumWidth(300)
            except Exception:
                pass

        # Adjust overall layout stretch to give label panel more width
        try:
            self.ui.horizontalLayout_5.setStretch(2, 2)  # previously 1
        except Exception:
            pass
        # Ensure label panel minimum width
        try:
            self.ui.label_plate.setMinimumWidth(340)
        except Exception:
            pass

    # Helpers for robust DICOM loading ---------------------------------------
    def _read_slice_array(self, ds):
        try:
            fp = getattr(ds, '_filepath', None)
            if not fp:
                # Fallback: assume ds already has pixel data
                full = ds
            else:
                full = pydicom.dcmread(fp, force=True, stop_before_pixels=False)
            arr = full.pixel_array
            # Multi-frame support
            if hasattr(ds, '_frame_index'):
                try:
                    arr = arr[getattr(ds, '_frame_index')]
                except Exception:
                    pass
            # Convert to float32 and apply rescale
            slope = getattr(full, 'RescaleSlope', 1) or 1
            intercept = getattr(full, 'RescaleIntercept', 0) or 0
            arr = arr.astype(np.float32)
            arr = arr * float(slope) + float(intercept)
            # Color to grayscale if needed
            if arr.ndim == 3 and arr.shape[-1] in (3, 4):
                arr = arr[..., :3].astype(np.float32)
                arr = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
            # MONOCHROME1 inversion
            photo = getattr(full, 'PhotometricInterpretation', None)
            if photo and str(photo).upper() == 'MONOCHROME1':
                amax = float(np.max(arr))
                amin = float(np.min(arr))
                arr = (amax + amin) - arr
            return arr
        except Exception as e:
            print(f"Failed reading slice array: {e}")
            return None

    def _get_spacing_from_ds(self, ds):
        try:
            fp = getattr(ds, '_filepath', None)
            d = pydicom.dcmread(fp, force=True, stop_before_pixels=True) if fp else ds
            ps = getattr(d, 'PixelSpacing', [1.0, 1.0])
            # DICOM: [row spacing (mm between centers of adjacent rows) -> y, column spacing -> x]
            sy = float(ps[0]) if len(ps) > 0 else 1.0
            sx = float(ps[1]) if len(ps) > 1 else sy
            return sx, sy
        except Exception:
            return 1.0, 1.0

    def _estimate_thickness_from_series(self, series):
        # Prefer series.thickness if set and can be cast to float
        try:
            if series.thickness not in (None, ''):
                return float(series.thickness)
        except Exception:
            pass
        # Fallback: compute from ImagePositionPatient Z diffs
        zs = []
        for s in series.slices:
            pos = getattr(s, 'ImagePositionPatient', None)
            if pos and len(pos) >= 3:
                try:
                    zs.append(float(pos[2]))
                except Exception:
                    pass
        if len(zs) >= 2:
            diffs = [abs(b - a) for a, b in zip(zs[:-1], zs[1:]) if abs(b - a) > 0]
            if diffs:
                import statistics
                return float(round(statistics.median(diffs), 3))
        return 1.0

    # ------------------------------------------------------------------------

    def eventFilter(self, watched, event):
        if getattr(self, '_is_closing', False):
            return False
        # Space key toggles single/multi view
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
            self._toggle_single_view(watched)
            return True
        # 2D slice views interaction (has update_pos)
        if watched in self.slice_wins:
            if self.ct_itk is None:
                return False
            if event.type() == QEvent.MouseMove:
                if self.slice_win_left_press:
                    if hasattr(watched, 'update_pos'):
                        tmp_idx = watched.update_pos()
                        tmp_type = ["axial", "coronal", "sagittal"]
                        for i, pos in enumerate(tmp_idx):
                            if pos > 0:
                                update_slice(self.ct_itk, tmp_type[i], pos, self.slice_wins[i], self.rec_datas)
                                self.slice_wins[i].win.Render()
                return False
            elif event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.slice_win_left_press = True
                    self.slice_win_left_release = False
                    if hasattr(watched, 'update_pos'):
                        tmp_idx = watched.update_pos()
                        tmp_type = ["axial","coronal","sagittal"]
                        for i,pos in enumerate(tmp_idx):
                            if pos > 0:
                                update_slice(self.ct_itk, tmp_type[i], pos, self.slice_wins[i],self.rec_datas)
                                self.slice_wins[i].win.Render()
                elif event.button() == Qt.RightButton:
                    self.slice_win_right_press = True
                    self.slice_win_right_release = False
                return False
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.slice_win_left_release = True
                    self.slice_win_left_press = False
                elif event.button() == Qt.RightButton:
                    self.slice_win_right_release = True
                    self.slice_win_right_press = False
                return False
        # 3D view: let VTK interactor handle mouse; only space key handled above
        if watched == self.model_win:
            return False
        return super().eventFilter(watched, event)

    # Single view toggle logic ------------------------------------------------
    def _toggle_single_view(self, watched):
        # Determine container widget for watched view
        if watched in self.slice_wins:
            idx = self.slice_wins.index(watched)
            container = [self.ui.win1, self.ui.win2, self.ui.win3][idx]
        elif watched == self.model_win:
            container = self.ui.win4
        else:
            return
        if not self.single_view_active:
            # Enter single view
            self.single_view_active = True
            self.single_view_widget = container
            # Hide other widgets
            for w in [self.ui.win1, self.ui.win2, self.ui.win3, self.ui.win4]:
                if w is not container:
                    w.hide()
            # Hide side panels and scrollbars
            self.ui.widget_2.hide()
            self.ui.label_plate.hide()
            self.ui.Bar1.hide(); self.ui.Bar2.hide(); self.ui.Bar3.hide()
            # Expand container
            container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Attach info label to container (if not win4)
            self._attach_info_label(container)
        else:
            # Restore multi-view
            self.single_view_active = False
            # Show all widgets
            for w in [self.ui.win1, self.ui.win2, self.ui.win3, self.ui.win4]:
                w.show()
            self.ui.widget_2.show()
            self.ui.label_plate.show()
            self.ui.Bar1.show(); self.ui.Bar2.show(); self.ui.Bar3.show()
            # Reattach info label to win4
            self._attach_info_label(self.ui.win4)
            self.single_view_widget = None

    def _attach_info_label(self, container):
        # Move info_label into the top of container's layout
        if container.layout() is None:
            lay = QVBoxLayout(container)
        else:
            lay = container.layout()
        if lay.indexOf(self.info_label) == -1:
            self.info_label.setParent(container)
            lay.insertWidget(0, self.info_label)
        self.info_label.show()

    def _clear_all_data(self):
        """清除所有已加载的数据和重建结果。"""
        # 移除所有VTK actors
        for act in self.actors:
            try:
                self.model_win.ren.RemoveActor(act)
            except Exception:
                pass
        self.actors.clear()

        # 清除标签面板中的ModelItemWidget
        label_layout = self.ui.verticalLayout
        for w in self.model_item_widgets:
            try:
                label_layout.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
            except Exception:
                pass
        self.model_item_widgets.clear()

        # 清除重建数据
        self.rec_datas.clear()

        # 清除CT数据
        self.ct_itk = None
        self.ct_data = None
        self.label_np = None
        self.lung_npy = None
        self.dicom_path = None
        self.patient_name = None

        # 重置信息标签
        self.info_label.setText("")

        # 清除切片视图（仅清除标签actors和mapper数据，保留slice_actor在渲染器中）
        for tmp_win in self.slice_wins:
            try:
                # 移除叠加的标签轮廓actors
                for lbl_act in tmp_win.label_actors:
                    tmp_win.img_ren.RemoveActor(lbl_act)
                tmp_win.label_actors = []
                # 将slice_mapper输入重置为空白，清除旧图像显示
                empty = vtk.vtkImageData()
                tmp_win.slice_mapper.SetInputData(empty)
                tmp_win.win.Render()
            except Exception:
                pass

        # 刷新3D视图
        try:
            self.model_win.ren.ResetCamera()
            self.model_win.win.Render()
        except Exception:
            pass

    def open_file(self):
        path = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if path:
            # 如果已有数据，弹窗确认是否清除
            if self.ct_itk is not None or len(self.rec_datas) > 0:
                reply = QMessageBox.question(
                    self, "确认加载新数据",
                    "当前已有加载的数据和重建结果，加载新数据将清除所有已有内容。\n\n是否继续？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                self._clear_all_data()

            self.dicom_path = path
            self.loader = DicomLoader(path)
            self.loader_thread = QThread()
            self.loader.moveToThread(self.loader_thread)
            self.loader_thread.started.connect(self.loader.run)
            self.loader.finished.connect(self.show_preview)
            self.loader.finished.connect(self.loader_thread.quit)
            self.loader_thread.start()

    def show_preview(self,series):
        preview_win = PreviewWindow(series)
        if preview_win.exec() == QDialog.Accepted:
            # Choose selected series
            tmp_series = getattr(preview_win, 'current_series', None)
            if tmp_series is None and preview_win.choose_idx is not None:
                tmp_series = preview_win.series_list[preview_win.choose_idx]
            if tmp_series is None or len(tmp_series.slices) == 0:
                QMessageBox.warning(self, "DICOM", "No slices to load in selected series.")
                return

            # Store patient name
            try:
                self.patient_name = str(tmp_series.name) if tmp_series.name else None
            except Exception:
                self.patient_name = None

            # Read first slice to define shape and spacing
            first_ds = tmp_series.slices[0]
            first_arr = self._read_slice_array(first_ds)
            if first_arr is None:
                QMessageBox.warning(self, "DICOM", "Failed to read first slice pixels.")
                return
            rows, cols = int(first_arr.shape[0]), int(first_arr.shape[1]) if first_arr.ndim == 2 else (first_arr.shape[0], first_arr.shape[1])

            slice_num = len(tmp_series.slices)
            tmp_volume = np.zeros((slice_num, rows, cols), dtype=np.float32)
            tmp_volume[0] = first_arr if first_arr.shape == (rows, cols) else first_arr[:rows, :cols]

            for i, tmp_slice in enumerate(tmp_series.slices[1:], start=1):
                arr = self._read_slice_array(tmp_slice)
                if arr is None:
                    continue
                if arr.shape != (rows, cols):
                    r = min(rows, arr.shape[0]); c = min(cols, arr.shape[1])
                    tmp_volume[i, :r, :c] = arr[:r, :c]
                else:
                    tmp_volume[i] = arr
            # tmp_volume = tmp_volume[:,::-1,:]
            sx, sy = self._get_spacing_from_ds(first_ds)
            sz = self._estimate_thickness_from_series(tmp_series)

            tmp_itk = sitk.GetImageFromArray(tmp_volume)
            tmp_itk.SetSpacing((sx, sy, sz))
            try:
                orient = getattr(first_ds, 'ImageOrientationPatient', None)
                pos = getattr(first_ds, 'ImagePositionPatient', None)
                if orient and pos and len(orient) >= 6 and len(pos) >= 3:
                    row = np.array(orient[:3], dtype=float)
                    col = np.array(orient[3:6], dtype=float)
                    normal = np.cross(row, col)
                    direction = [
                        float(row[0]), float(row[1]), float(row[2]),
                        float(col[0]), float(col[1]), float(col[2]),
                        float(normal[0]), float(normal[1]), float(normal[2])
                    ]
                    tmp_itk.SetDirection(direction)
                    tmp_itk.SetOrigin((float(pos[0]), float(pos[1]), float(pos[2])))
                    print("[Orientation] Row:", row, "Col:", col, "Normal:", normal, "Direction:", direction)
                else:
                    tmp_itk.SetOrigin((0.0, 0.0, 0.0))
                    print("[Orientation] Missing orientation tags - using default origin.")
            except Exception as e:
                tmp_itk.SetOrigin((0.0, 0.0, 0.0))
                print(f"[Orientation] Failed to set direction/origin: {e}")

            self.ct_itk = tmp_itk
            self.ct_data = tmp_volume
            # sitk.WriteImage(self.ct_itk,"temp_ct.nii.gz")
            self.info.spacing = np.array(self.ct_itk.GetSpacing())
            self.info.dim = np.array(self.ct_itk.GetSize())
            self.info.origin = np.array(self.ct_itk.GetOrigin())

            # Update sliders
            self.axial_slider.setRange(0, self.ct_data.shape[0] - 1)
            self.coronal_slider.setRange(0, self.ct_data.shape[1] - 1)
            self.sagittal_slider.setRange(0, self.ct_data.shape[2] - 1)

            self.axial_slider.setValue(self.ct_data.shape[0] // 2)
            self.coronal_slider.setValue(self.ct_data.shape[1] // 2)
            self.sagittal_slider.setValue(self.ct_data.shape[2] // 2)

            # 强制刷新切片（即使滑块值未变，也要显示新数据）
            self.update_axial_slice()
            self.update_coronal_slice()
            self.update_sagittal_slice()

            # Reset cameras and render
            for tmp_win in self.slice_wins:
                tmp_win.img_ren.ResetCamera()
                tmp_win.win.Render()

            # Optionally apply default window/level from config (lung)
            try:
                self.change_win_level("lung")
            except Exception:
                pass

            # Update info label after volume load
            self._update_info_label()
        # else: user canceled, do nothing

    def _update_info_label(self):
        name_part = f"Patient: {self.patient_name}" if self.patient_name else "Patient: Unknown"
        path_part = f"Path: {self.dicom_path}" if self.dicom_path else "Path: -"
        self.info_label.setText(f"{name_part}  |  {path_part}")
        self.info_label.adjustSize()

    # Highlight and focus helpers -------------------------------------------
    def _highlight_actor(self, actor:vtk.vtkActor):
        try:
            prop = actor.GetProperty()
            prop.SetEdgeVisibility(1)
            prop.SetEdgeColor(1,1,0.6)
            prop.SetLineWidth(2.0)
            self.model_win.win.Render()
        except Exception:
            pass

    def _unhighlight_actor(self, actor:vtk.vtkActor):
        try:
            prop = actor.GetProperty()
            prop.SetEdgeVisibility(0)
            prop.SetLineWidth(1.0)
            self.model_win.win.Render()
        except Exception:
            pass

    def _focus_actor(self, actor:vtk.vtkActor):
        try:
            self.model_win.ren.ResetCamera()  # simple reset around all actors
            self.model_win.ren.ResetCameraClippingRange()
            self.model_win.win.Render()
        except Exception:
            pass

    def update_axial_slice(self):
        slice_index = self.axial_slider.value()
        if self.ct_itk:
            update_slice(self.ct_itk, 'axial', slice_index, self.slice_wins[0],self.rec_datas)
            self.slice_wins[0].win.Render()


    def update_coronal_slice(self):
        slice_index = self.coronal_slider.value()
        if self.ct_itk:
            update_slice(self.ct_itk, 'coronal', slice_index, self.slice_wins[1],self.rec_datas)
            self.slice_wins[1].win.Render()


    def update_sagittal_slice(self):
        slice_index = self.sagittal_slider.value()
        if self.ct_itk:
            update_slice(self.ct_itk, 'sagittal', slice_index, self.slice_wins[2],self.rec_datas)
            self.slice_wins[2].win.Render()

    def secret_config(self):
        tmp_path = os.path.join(os.path.expanduser("~"),".3dnav")
        key_path = os.path.join(tmp_path,"3dnav_key")

        if not os.path.exists(tmp_path) or not os.path.exists(key_path):
            self.ui.btn_autorec.setEnabled(False)
        else:
            with open(key_path,"r") as f:
                key = json.load(f)
                if "lung_rec" in key.keys():
                    lung_rec_key = key["lung_rec"]
                    if decrypted_secret_key(lung_rec_key,0):
                        self.ui.btn_autorec.setEnabled(True)




    def auto_rec_all(self):

        models = self.config["models"][self.type]
        label_layout = self.ui.verticalLayout

        # Progress dialog setup
        progress = QProgressDialog("Starting reconstruction...", "Cancel", 0, 100, self)
        self._recon_progress = progress
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        self.lung_npy = []

        total_models = max(1, len(models))
        for m_idx, tmp_model in enumerate(models, start=1):
            if progress.wasCanceled():
                break
            base = int((m_idx - 1) * (100 / total_models))
            chunk = int(100 / total_models)
            # Step 1: inference
            progress.setLabelText(f"[{m_idx}/{total_models}] Running model '{tmp_model}' (inference)...")
            progress.setValue(min(99, base + int(chunk * 0.05)))
            QApplication.processEvents()

            if tmp_model == "nodule":
                continue

            try:
                tmp_seg_data = rec_all(self.ct_itk, tmp_model)

                # sitk.WriteImage(tmp_seg_data,f'temp_{tmp_model}_seg.nii.gz')
            except Exception as e:
                QMessageBox.warning(self, "Reconstruction", f"Model '{tmp_model}' failed: {e}")
                continue

            progress.setValue(min(99, base + int(chunk * 0.55)))
            QApplication.processEvents()

            tmp_seg_npy = sitk.GetArrayFromImage(tmp_seg_data)
            label_id = np.unique(tmp_seg_npy.reshape(-1)).astype(int)
            tmp_keys = [int(i) for i in self.config["tags"][self.type][tmp_model].keys()]

            # Count tasks for this model's labels
            tasks = [lid for lid in label_id if lid in tmp_keys]
            total_tasks = max(1, len(tasks))
            done_tasks = 0

            for tmp_id in tasks:
                if progress.wasCanceled():
                    break
                progress.setLabelText(f"[{m_idx}/{total_models}] Building '{tmp_model}' label {tmp_id} ({done_tasks+1}/{total_tasks})...")
                # Step 2: build mask
                tmp_data = np.zeros_like(tmp_seg_npy)
                tmp_data[tmp_seg_npy==tmp_id] = 1

                if "lung" == tmp_model:
                    self.lung_npy.append(tmp_data)
                elif "nodule" == tmp_model and self.lung_npy is not None:
                    tmp_mask = np.zeros_like(tmp_data)
                    for tmp_lung in self.lung_npy:
                        tmp_mask[tmp_lung==1] = 1
                    tmp_data = tmp_data * tmp_mask

                # Step 3: mesh build & actor
                tmp_itk = sitk.GetImageFromArray(tmp_data)
                tmp_itk.CopyInformation(tmp_seg_data)
                tmp_poly = MeshProcess.itk2polydata(tmp_itk)

                tmp_prop = self.config["tags"][self.type][tmp_model][str(tmp_id)]
                tmp_smooth_poly = MeshProcess.mesh_smooth(tmp_poly,int(tmp_prop["smooth_type"]))
                tmp_act = MeshProcess.polydata2act(tmp_smooth_poly)
                tmp_act.label_name = tmp_prop["name"]
                tmp_act.GetProperty().SetColor(tmp_prop['color'])
                tmp_act.GetProperty().SetDiffuse(0)
                tmp_act.GetProperty().SetSpecular(1)
                self.actors.append(tmp_act)
                self.model_win.ren.AddActor(tmp_act)

                tmp_rec_data = RecData()
                tmp_rec_data.name = tmp_prop["name"]
                tmp_rec_data.mask = tmp_data
                tmp_rec_data.actor = tmp_act
                tmp_rec_data.color = tmp_prop['color']
                self.rec_datas.append(tmp_rec_data)

                widget = self.create_label(tmp_act.label_name,tmp_act,tmp_prop['color'])
                label_layout.insertWidget(label_layout.count()-1, widget)

                done_tasks += 1
                # Update progress inside this model chunk: 55% -> 95%
                inner = base + int(chunk * (0.55 + 0.4 * (done_tasks/total_tasks)))
                progress.setValue(min(99, inner))
                QApplication.processEvents()

            # Per-model finishing
            progress.setLabelText(f"[{m_idx}/{total_models}] Finalizing '{tmp_model}'...")
            progress.setValue(min(99, base + int(chunk * 0.98)))
            QApplication.processEvents()

        progress.setLabelText("Reconstruction done.")
        progress.setValue(100)
        QApplication.processEvents()
        progress.close()

        # Refresh views
        self.update_axial_slice()
        self.update_coronal_slice()
        self.update_sagittal_slice()
        self.model_win.ren.ResetCamera()
        self.model_win.win.Render()


    def create_label(self,label_name,actor,color=None):
        widget = ModelItemWidget(label_name, actor, color if color is not None else (200,200,200),
                                 on_focus=self._focus_actor,
                                 on_highlight=self._highlight_actor,
                                 on_unhighlight=self._unhighlight_actor)
        self.model_item_widgets.append(widget)
        return widget

    # =================== Watershed Analysis ================================
    # 18段支气管分级ID与名称映射
    SEGMENT_NAMES = {
        1: 'right_S1', 2: 'right_S2', 3: 'right_S3', 4: 'right_S4', 5: 'right_S5',
        6: 'right_S6', 7: 'right_S7', 8: 'right_S8', 9: 'right_S9', 10: 'right_S10',
        11: 'left_S1+2', 12: 'left_S3', 13: 'left_S4', 14: 'left_S5', 15: 'left_S6',
        16: 'left_S7+8', 17: 'left_S9', 18: 'left_S10'
    }
    # 每个肺叶对应的分级段ID
    LOBE_SEGMENT_IDS = {
        "ru_lobe": [1, 2, 3],              # 右上肺叶: S1, S2, S3
        "rm_lobe": [4, 5],                 # 右中肺叶: S4, S5
        "rl_lobe": [6, 7, 8, 9, 10],       # 右下肺叶: S6~S10
        "lu_lobe": [11, 12],               # 左上肺叶: S1+2, S3
        "ll_lobe": [13, 14, 15, 16, 17, 18],  # 左下肺叶: S4, S5, S6, S7+8, S9, S10
    }

    def _preprocess_bronchus_mask(self, bronchus_mask, lung_masks):
        """预处理支气管mask：去除肺外的离散噪声。
        将支气管mask与所有肺叶mask的并集做交集，只保留肺内的部分，
        然后进行连通域分析，去除小的离散噪声。
        """
        from scipy import ndimage

        # 合并所有肺叶mask得到完整肺区域
        lung_union = np.zeros_like(bronchus_mask, dtype=np.uint8)
        for lm in lung_masks:
            lung_union[lm > 0] = 1

        # 对肺区域做适当膨胀，允许支气管稍微超出肺叶边界
        struct = ndimage.generate_binary_structure(3, 2)
        lung_dilated = ndimage.binary_dilation(lung_union, structure=struct, iterations=5).astype(np.uint8)

        # 支气管与膨胀后肺区域取交集
        cleaned = (bronchus_mask > 0).astype(np.uint8) * lung_dilated

        # # 连通域分析，去除小的离散噪声
        # labeled_array, num_features = ndimage.label(cleaned)
        # if num_features > 1:
        #     # 保留最大连通域
        #     component_sizes = ndimage.sum(cleaned, labeled_array, range(1, num_features + 1))
        #     largest_label = np.argmax(component_sizes) + 1
        #     cleaned = (labeled_array == largest_label).astype(np.uint8)

        return cleaned

    def watershed_analysis(self):
        """流域分析 - 默认使用支气管进行分级和肺段划分"""
        if self.ct_itk is None:
            QMessageBox.warning(self, "流域分析", "请先加载CT数据。")
            return
        if len(self.rec_datas) == 0:
            QMessageBox.warning(self, "流域分析", "请先执行自动重建。")
            return

        # --- 1. 确定选择的肺叶 ---
        lobe_idx = self.ui.combo_lobe.currentIndex()  # 0~4

        # 肺叶名称映射 (与config.json中的lung标签对应)
        lobe_name_map = {
            0: ("ru_lobe", "右上肺叶"),
            1: ("rm_lobe", "右中肺叶"),
            2: ("rl_lobe", "右下肺叶"),
            3: ("lu_lobe", "左上肺叶"),
            4: ("ll_lobe", "左下肺叶"),
        }
        lobe_key, lobe_display_name = lobe_name_map[lobe_idx]

        # 该肺叶对应的分级段ID列表
        target_seg_ids = self.LOBE_SEGMENT_IDS[lobe_key]

        # --- 2. 从rec_datas中找到支气管和肺叶mask ---
        bronchus_mask = None
        lobe_mask = None
        lung_masks = []  # 收集所有肺叶mask用于预处理
        all_lobe_keys = ["ru_lobe", "rm_lobe", "rl_lobe", "lu_lobe", "ll_lobe"]

        for rd in self.rec_datas:
            if rd.name == "bronchus":
                bronchus_mask = rd.mask
            if rd.name == lobe_key:
                lobe_mask = rd.mask
            if rd.name in all_lobe_keys:
                lung_masks.append(rd.mask)

        if bronchus_mask is None:
            QMessageBox.warning(self, "流域分析", "未找到支气管的重建数据，请先完成自动重建。")
            return
        if lobe_mask is None:
            QMessageBox.warning(self, "流域分析", f"未找到{lobe_display_name}的重建数据，请先完成自动重建。")
            return

        # --- Progress dialog ---
        progress = QProgressDialog("正在进行流域分析...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        tmp_dir = None  # 临时目录，用于finally中清理
        try:
            # --- 3. 预处理支气管：去除肺外离散噪声 ---
            progress.setLabelText("正在预处理支气管（去除肺外噪声）...")
            progress.setValue(3)
            QApplication.processEvents()

            cleaned_bronchus = bronchus_mask
            # cleaned_bronchus = self._preprocess_bronchus_mask(bronchus_mask, lung_masks)

            if np.sum(cleaned_bronchus) == 0:
                QMessageBox.warning(self, "流域分析", "预处理后支气管数据为空，请检查重建结果。")
                return

            if progress.wasCanceled():
                return

            # --- 4. 将预处理后的支气管mask保存为nii.gz ---
            progress.setLabelText("正在准备支气管数据...")
            progress.setValue(8)
            QApplication.processEvents()

            tmp_dir = tempfile.mkdtemp(prefix="watershed_")
            bronchus_nii_path = os.path.join(tmp_dir, "bronchus_input.nii.gz")
            output_folder = os.path.join(tmp_dir, "output")
            os.makedirs(output_folder, exist_ok=True)

            bronchus_itk = sitk.GetImageFromArray(cleaned_bronchus.astype(np.uint8))
            bronchus_itk.CopyInformation(self.ct_itk)
            sitk.WriteImage(bronchus_itk, bronchus_nii_path)

            if progress.wasCanceled():
                return

            # --- 5. 调用new_nii_infer.exe进行支气管分级 (type=0: airway) ---
            progress.setLabelText("正在执行支气管分级（可能需要几分钟）...")
            progress.setValue(15)
            QApplication.processEvents()

            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "pulmonary_infer", "new_nii_infer.exe")
            if not os.path.exists(exe_path):
                QMessageBox.warning(self, "流域分析", f"未找到推理程序: {exe_path}")
                return

            cmd = [
                exe_path,
                "-i", bronchus_nii_path,
                "-t", "0",  # type=0 表示airway(支气管)
                "-o", output_folder
            ]
            print(f"[Watershed] Running: {' '.join(cmd)}")

            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 等待进程完成，同时保持UI响应
            while proc.poll() is None:
                QApplication.processEvents()
                if progress.wasCanceled():
                    proc.terminate()
                    return
                import time
                time.sleep(0.3)

            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                err_msg = stderr.decode('utf-8', errors='replace') if stderr else 'Unknown error'
                QMessageBox.warning(self, "流域分析", f"支气管分级失败:\n{err_msg}")
                return

            print(f"[Watershed] stdout: {stdout.decode('utf-8', errors='replace')}")

            # --- 6. 读取分级结果 ---
            progress.setLabelText("正在读取分级结果...")
            progress.setValue(55)
            QApplication.processEvents()

            result_path = os.path.join(output_folder, "result.nii")
            if not os.path.exists(result_path):
                QMessageBox.warning(self, "流域分析", f"未找到分级结果文件: {result_path}")
                return

            result_itk = sitk.ReadImage(result_path)
            result_npy = sitk.GetArrayFromImage(result_itk)  # 支气管分级体数据 (18段)

    
            progress.setLabelText(f"正在筛选{lobe_display_name}对应的分级段...")
            progress.setValue(58)
            QApplication.processEvents()


            filtered_result = np.zeros_like(result_npy, dtype=result_npy.dtype)
            for seg_id in target_seg_ids:
                filtered_result[result_npy == seg_id] = seg_id


            progress.setLabelText("正在计算...")
            progress.setValue(60)
            QApplication.processEvents()


            vessel_labeled_coords = np.argwhere(filtered_result > 0)  # (N, 3)
            vessel_labels = filtered_result[filtered_result > 0]       # (N,)

            if len(vessel_labeled_coords) == 0:
                QMessageBox.warning(self, "流域分析",
                    f"在分级结果中未找到{lobe_display_name}对应的段（ID: {target_seg_ids}），无法进行分类。")
                return


            lobe_coords = np.argwhere(lobe_mask > 0)  # (M, 3)
            if len(lobe_coords) == 0:
                QMessageBox.warning(self, "流域分析", f"{lobe_display_name}体素为空。")
                return


            lobe_set = set(map(tuple, lobe_coords))
            in_lobe_mask = np.array([tuple(c) in lobe_set for c in vessel_labeled_coords])

            if np.sum(in_lobe_mask) > 0:
                tree_coords = vessel_labeled_coords[in_lobe_mask]
                tree_labels = vessel_labels[in_lobe_mask]
            else:

                tree_coords = vessel_labeled_coords
                tree_labels = vessel_labels

            progress.setLabelText("正在计算...")
            progress.setValue(70)
            QApplication.processEvents()

            tree = cKDTree(tree_coords)
            _, indices = tree.query(lobe_coords, k=1)
            lobe_segment_labels = tree_labels[indices]


            segment_volume = np.zeros_like(lobe_mask, dtype=np.float32)
            for i, coord in enumerate(lobe_coords):
                segment_volume[coord[0], coord[1], coord[2]] = lobe_segment_labels[i]

            if progress.wasCanceled():
                return


            progress.setLabelText("正在重建...")
            progress.setValue(80)
            QApplication.processEvents()

            # 只处理当前肺叶对应的段ID
            unique_labels = sorted(target_seg_ids)

            # 为每个分段生成不同颜色
            segment_colors = self._generate_segment_colors(len(unique_labels))

            label_layout = self.ui.verticalLayout
            total_segs = max(1, len(unique_labels))

            for seg_idx, seg_label in enumerate(unique_labels):
                if progress.wasCanceled():
                    break
                seg_display = self.SEGMENT_NAMES.get(seg_label, f"S{seg_label}")
                progress.setLabelText(f"正在处理 {seg_display} ({seg_idx+1}/{total_segs})...")
                seg_progress = 80 + int(18 * (seg_idx / total_segs))
                progress.setValue(min(99, seg_progress))
                QApplication.processEvents()

                # 提取该分段的mask
                seg_mask = np.zeros_like(segment_volume, dtype=np.uint8)
                seg_mask[segment_volume == seg_label] = 1

                if np.sum(seg_mask) < 10:
                    continue  # 跳过太小的分段

                # 等值面提取
                seg_itk = sitk.GetImageFromArray(seg_mask)
                seg_itk.CopyInformation(self.ct_itk)
                seg_poly = MeshProcess.itk2polydata(seg_itk)

                # 使用肺叶相同的平滑方案 (smooth_type=2)
                seg_smooth_poly = MeshProcess.mesh_smooth(seg_poly, 2)

                seg_color = segment_colors[seg_idx % len(segment_colors)]
                seg_act = MeshProcess.polydata2act(seg_smooth_poly)
                seg_name = self.SEGMENT_NAMES.get(seg_label, f"{lobe_display_name}_S{seg_label}")
                seg_act.label_name = seg_name
                seg_act.GetProperty().SetColor(seg_color)
                seg_act.GetProperty().SetDiffuse(0)
                seg_act.GetProperty().SetSpecular(1)

                self.actors.append(seg_act)
                self.model_win.ren.AddActor(seg_act)

                tmp_rec_data = RecData()
                tmp_rec_data.name = seg_name
                tmp_rec_data.mask = seg_mask
                tmp_rec_data.actor = seg_act
                tmp_rec_data.color = seg_color
                self.rec_datas.append(tmp_rec_data)

                widget = self.create_label(seg_name, seg_act, seg_color)
                label_layout.insertWidget(label_layout.count() - 1, widget)

            # --- 隐藏对应肺叶标签 ---
            for w in self.model_item_widgets:
                if w.name == lobe_key:
                    w.set_visibility(False)
                    w.slider.setValue(0)  # 透明度设为0
                    break

            progress.setLabelText("流域分析完成。")
            progress.setValue(100)
            QApplication.processEvents()
            progress.close()

            # 刷新显示
            self.update_axial_slice()
            self.update_coronal_slice()
            self.update_sagittal_slice()
            self.model_win.ren.ResetCamera()
            self.model_win.win.Render()

        except Exception as e:
            progress.close()
            QMessageBox.warning(self, "流域分析", f"流域分析过程出错:\n{str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理临时文件
            if tmp_dir and os.path.exists(tmp_dir):
                try:
                    shutil.rmtree(tmp_dir)
                    print(f"[Watershed] 已清理临时目录: {tmp_dir}")
                except Exception as cleanup_err:
                    print(f"[Watershed] 清理临时目录失败: {cleanup_err}")

    def _generate_segment_colors(self, n):
        """为n个肺段生成差异明显的颜色"""
        base_colors = [
            [0.9, 0.3, 0.3],   # 红
            [0.3, 0.9, 0.3],   # 绿
            [0.3, 0.3, 0.9],   # 蓝
            [0.9, 0.9, 0.2],   # 黄
            [0.9, 0.3, 0.9],   # 品红
            [0.3, 0.9, 0.9],   # 青
            [1.0, 0.6, 0.2],   # 橙
            [0.6, 0.2, 1.0],   # 紫
            [0.2, 1.0, 0.6],   # 春绿
            [1.0, 0.4, 0.6],   # 粉
            [0.4, 0.6, 1.0],   # 天蓝
            [0.8, 1.0, 0.3],   # 黄绿
            [1.0, 0.7, 0.5],   # 杏色
            [0.5, 0.7, 1.0],   # 浅蓝
            [0.7, 0.5, 0.3],   # 棕
            [0.5, 1.0, 0.7],   # 薄荷
            [0.8, 0.4, 0.8],   # 淡紫
            [0.4, 0.8, 0.4],   # 淡绿
            [0.9, 0.5, 0.1],   # 深橙
        ]
        colors = []
        for i in range(n):
            colors.append(base_colors[i % len(base_colors)])
        return colors

    # Helpers to finalize VTK widgets safely
    def _finalize_qvtk(self, widget):
        try:
            win = widget.GetRenderWindow()
            if win is not None:
                try:
                    # Remove all view props
                    rens = win.GetRenderers()
                    if rens is not None:
                        rens.InitTraversal()
                        ren = rens.GetNextItem()
                        while ren is not None:
                            try:
                                ren.RemoveAllViewProps()
                            except Exception:
                                pass
                            ren = rens.GetNextItem()
                except Exception:
                    pass
                try:
                    iren = win.GetInteractor()
                    if iren is not None:
                        iren.Disable()
                except Exception:
                    pass
                try:
                    win.Finalize()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            widget.deleteLater()
        except Exception:
            pass

    def closeEvent(self, event):
        # Prevent event handling during teardown
        self._is_closing = True
        # Stop potential loader thread
        try:
            if hasattr(self, 'loader_thread') and self.loader_thread is not None:
                if self.loader_thread.isRunning():
                    try:
                        self.loader_thread.requestInterruption()
                    except Exception:
                        pass
                    self.loader_thread.quit()
                    self.loader_thread.wait(2000)
        except Exception:
            pass
        # Disconnect signals (buttons, sliders)
        try:
            self.axial_slider.valueChanged.disconnect()
            self.coronal_slider.valueChanged.disconnect()
            self.sagittal_slider.valueChanged.disconnect()
        except Exception:
            pass
        try:
            self.ui.btn_input_data.clicked.disconnect()
            self.ui.btn_autorec.clicked.disconnect()
            self.ui.btn_watershed.clicked.disconnect()
        except Exception:
            pass
        # Disconnect signals from slice windows
        try:
            for i, tmp_win in enumerate(getattr(self, 'slice_wins', [])):
                try:
                    tmp_win.signal_wheel.disconnect()

                except Exception:
                    pass
        except Exception:
            pass
        # Cancel reconstruction progress dialog if active
        try:
            prog = getattr(self, '_recon_progress', None)
            if prog is not None:
                try: prog.cancel()
                except Exception: pass
                try: prog.close()
                except Exception: pass
        except Exception:
            pass
        # Finalize VTK widgets (call widget cleanup before delete)
        try:
            for tmp_win in getattr(self, 'slice_wins', []):
                try:
                    tmp_win.cleanup()
                    tmp_win.Finalize()
                except Exception: pass
        except Exception:
            pass
        try:
            if hasattr(self, 'model_win') and self.model_win is not None:
                try:
                    self.model_win.cleanup()
                    self.model_win.Finalize()
                except Exception: pass
        except Exception:
            pass
        # Proceed with default close
        super().closeEvent(event)

    def show_poly(self,poly):
        tmp_mapper = vtk.vtkPolyDataMapper()
        tmp_mapper.SetInputData(poly)

        tmp_actor = vtk.vtkActor()
        tmp_actor.SetMapper(tmp_mapper)
        tmp_actor.GetProperty().SetColor(1,0,0)
        tmp_actor.GetProperty().SetDiffuse(1)
        tmp_actor.GetProperty().SetSpecular(0)
        tmp_actor.SetPickable(0)

        tmp_ren = vtk.vtkRenderer()
        tmp_ren.AddActor(tmp_actor)
        tmp_ren.SetBackground(1,1,1)

        cam:vtk.vtkCamera = tmp_ren.GetActiveCamera()
        cam.SetParallelProjection(1)

        tmp_ren.ResetCamera()

        tmp_win = vtk.vtkRenderWindow()
        tmp_win.AddRenderer(tmp_ren)
        # tmp_win.SetInteractor(None)

        tmp_interactor = vtk.vtkRenderWindowInteractor()
        tmp_interactor.SetRenderWindow(tmp_win)

        tmp_win.Render()

        tmp_interactor.Start()

    def change_win_level(self,type:str):
        window_level = self.config["window_level"]
        if type in window_level.keys():
            for tmp_win in self.slice_wins:
                tmp_win.slice_actor.GetProperty().SetColorWindow(window_level[type]["window"])
                tmp_win.slice_actor.GetProperty().SetColorLevel(window_level[type]["level"])
                tmp_win.win.Render()



    def export_stl(self):

        path = QFileDialog.getExistingDirectory(self, "Open Directory", "")



        for tmp_data in self.rec_datas:

            tmp_actor = tmp_data.actor
            tmp_poly = tmp_actor.GetMapper().GetInput()
            tmp_stl = vtk.vtkSTLWriter()
            tmp_stl.SetFileName(f"{path}/{tmp_data.name}.stl")
            tmp_stl.SetInputData(tmp_poly)
            tmp_stl.SetFileTypeToBinary()
            tmp_stl.Write()


        Msgbox = QMessageBox()
        Msgbox.setText("Export stl done")
        Msgbox.exec()

    def _slot_wheel(self, slider,val):
        value = slider.value() + val
        if value < 0 or value > slider.maximum():
            return

        slider.setValue(value)
