import os
import pydicom
from pydicom.errors import InvalidDicomError
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import numpy as np
import vtkmodules.util.numpy_support as npys
from basewindow import SliceWin3


class DicomSeries:
    def __init__(self):
        self.slices = []
        self.series_uid = ""
        self.name = ""
        self.patient_id = ""
        self.date = ""
        self.thickness = ""
        self.modality = ""
        self.orientation = []

    @property
    def slice_count(self):
        return len(self.slices)


class DicomLoader(QObject):
    progress = Signal(int)
    finished = Signal(list)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def _safe_get(self, ds, attr, default=""):
        return getattr(ds, attr, default)

    def _sort_slices(self, slices):
        if not slices:
            return slices
        # Try orientation-aware sorting
        first = slices[0]
        orient = getattr(first, 'ImageOrientationPatient', None)
        positions = []
        if orient and isinstance(orient, (list, tuple)) and len(orient) >= 6:
            try:
                row_vec = np.array(orient[:3], dtype=float)
                col_vec = np.array(orient[3:6], dtype=float)
                normal = np.cross(row_vec, col_vec)
                # Collect (slice, projected_position)
                for s in slices:
                    pos = getattr(s, 'ImagePositionPatient', None)
                    if pos and len(pos) >= 3:
                        try:
                            proj = float(np.dot(normal, np.array(pos[:3], dtype=float)))
                            positions.append((s, proj))
                        except Exception:
                            pass
                if len(positions) == len(slices):
                    # Sort by projection; handle descending acquisition
                    positions.sort(key=lambda x: x[1])
                    sorted_slices = [p[0] for p in positions]
                    return sorted_slices
            except Exception:
                pass
        # Fallback original logic
        def key(ds):
            pos = getattr(ds, 'ImagePositionPatient', None)
            if pos and len(pos) >= 3:
                try:
                    return float(pos[2])
                except Exception:
                    pass
            if hasattr(ds, 'InstanceNumber'):
                try:
                    return int(ds.InstanceNumber)
                except Exception:
                    pass
            return slices.index(ds)
        try:
            return sorted(slices, key=key)
        except Exception:
            return slices

    def _estimate_thickness(self, series):
        positions = []
        for s in series.slices:
            pos = getattr(s, 'ImagePositionPatient', None)
            if pos and len(pos) >= 3:
                try:
                    positions.append(float(pos[2]))
                except Exception:
                    pass
        if len(positions) >= 2:
            diffs = sorted([abs(b - a) for a, b in zip(positions[:-1], positions[1:]) if abs(b - a) > 0])
            if diffs:
                import statistics
                return str(round(statistics.median(diffs), 3))
        return ''

    def run(self):
        series_dict = {}
        total_files = sum(len(files) for _, _, files in os.walk(self.path)) or 1
        processed = 0
        current_thread = QThread.currentThread()
        for root, _, files in os.walk(self.path):
            if current_thread.isInterruptionRequested():
                break
            for file in files:
                if current_thread.isInterruptionRequested():
                    break
                processed += 1
                if processed % 10 == 0:
                    self.progress.emit(int(processed / total_files * 100))
                fp = os.path.join(root, file)
                try:
                    # Read only headers first for speed and robustness
                    ds = pydicom.dcmread(fp, force=True, stop_before_pixels=True)
                    if not hasattr(ds, 'SeriesInstanceUID'):
                        continue

                    uid = ds.SeriesInstanceUID
                    if uid not in series_dict:
                        series = DicomSeries()
                        series.series_uid = uid
                        series.patient_id = self._safe_get(ds, 'PatientID', 'Unnamed')
                        series.name = str(self._safe_get(ds, 'PatientName', 'Unnamed'))
                        series.date = self._safe_get(ds, 'StudyDate', '')
                        raw_thickness = self._safe_get(ds, 'SliceThickness', '')
                        series.thickness = str(raw_thickness) if raw_thickness != '' else ''
                        series.modality = self._safe_get(ds, 'Modality', '')
                        series.orientation = self._safe_get(ds, 'ImageOrientationPatient', [1, 0, 0, 0, 1, 0])
                        series_dict[uid] = series

                    # Multi-frame: create shallow copies with frame index (without loading pixel data)
                    n_frames = 1
                    try:
                        n_frames = int(getattr(ds, 'NumberOfFrames', 1) or 1)
                    except Exception:
                        n_frames = 1
                    if n_frames > 1:
                        for frame_index in range(n_frames):
                            try:
                                frame_ds = ds.copy()
                            except Exception:
                                frame_ds = ds
                            setattr(frame_ds, '_frame_index', frame_index)
                            setattr(frame_ds, '_filepath', fp)
                            series_dict[uid].slices.append(frame_ds)
                    else:
                        setattr(ds, '_filepath', fp)
                        series_dict[uid].slices.append(ds)
                except (InvalidDicomError, Exception):
                    continue
        # Sort slices and compute missing thickness
        for series in series_dict.values():
            series.slices = self._sort_slices(series.slices)
            if not series.thickness:
                series.thickness = self._estimate_thickness(series)
        self.progress.emit(100)
        self.finished.emit(list(series_dict.values()))


class PreviewWindow(QDialog):
    def __init__(self, series_list, parent=None):
        super().__init__(parent)
        self.series_list = series_list
        self.current_series = None
        self.choose_idx = None
        self._manual_window = None
        self._manual_level = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("DICOM Preview")
        self.resize(1400, 900)

        # Main layout
        main_layout = QHBoxLayout()

        # Left side (VTK + slice slider + window/level controls)
        left_layout = QVBoxLayout()

        self.vtk_widget = SliceWin3(self)
        # Connect wheel from VTK to change current slice
        self.vtk_widget.signal_wheel.connect(lambda step: self.slice_slider.setValue(min(max(self.slice_slider.value() + step, self.slice_slider.minimum()), self.slice_slider.maximum())))

        # Slice slider
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.valueChanged.connect(self.update_slice)
        # Slice label
        self.slice_label = QLabel("Slice: -/-")
        self.slice_label.setAlignment(Qt.AlignCenter)

        # Window/Level controls
        wl_group = QGroupBox("Window / Level")
        wl_layout = QGridLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            'From DICOM', 'Auto', 'Brain', 'Lung', 'Mediastinum', 'Abdomen', 'Bone', 'Liver', 'Soft Tissue'
        ])

        self.window_spin = QSpinBox()
        self.window_spin.setRange(1, 50000)
        self.window_spin.setValue(1200)
        self.level_spin = QSpinBox()
        self.level_spin.setRange(-5000, 5000)
        self.level_spin.setValue(-400)

        apply_btn = QPushButton('Apply')
        apply_btn.clicked.connect(self.apply_manual_window_level)
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)

        wl_layout.addWidget(QLabel('Preset:'), 0, 0)
        wl_layout.addWidget(self.preset_combo, 0, 1, 1, 2)
        wl_layout.addWidget(QLabel('Window:'), 1, 0)
        wl_layout.addWidget(self.window_spin, 1, 1)
        wl_layout.addWidget(QLabel('Level:'), 1, 2)
        wl_layout.addWidget(self.level_spin, 1, 3)
        wl_layout.addWidget(apply_btn, 2, 0, 1, 4)
        wl_group.setLayout(wl_layout)

        left_layout.addWidget(self.vtk_widget)
        left_layout.addWidget(self.slice_slider)
        left_layout.addWidget(self.slice_label)
        left_layout.addWidget(wl_group)

        # Right side (Series table)
        right_layout = QVBoxLayout()

        self.series_table = QTableWidget()
        self.series_table.setColumnCount(6)
        self.series_table.setHorizontalHeaderLabels(["Name", "ID", "Date", "Thickness", "Modality", "Slices"])
        self.series_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.series_table.clicked.connect(self.load_series)
        self.series_table.horizontalHeader().setStretchLastSection(True)
        self.series_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for i, series in enumerate(self.series_list):
            self.series_table.insertRow(i)
            self.series_table.setItem(i, 0, QTableWidgetItem(str(series.name)))
            self.series_table.setItem(i, 1, QTableWidgetItem(series.patient_id or ''))
            self.series_table.setItem(i, 2, QTableWidgetItem(series.date or ''))
            self.series_table.setItem(i, 3, QTableWidgetItem(str(series.thickness or '')))
            self.series_table.setItem(i, 4, QTableWidgetItem(series.modality or ''))
            self.series_table.setItem(i, 5, QTableWidgetItem(str(series.slice_count)))

        right_layout.addWidget(self.series_table)

        # Buttons bottom
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self._on_reject)

        # Assemble main layout
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        # Select first series
        if self.series_list:
            self.series_table.selectRow(0)
            self.load_series(self.series_table.model().index(0, 0))
    def _on_accept(self):
        # Require all three phases selected
        self.vtk_widget.Finalize()
        self.accept()

    def _on_reject(self):
        self.vtk_widget.Finalize()
        self.reject()


    def closeEvent(self, arg__1):
        try:
            if hasattr(self, 'vtk_widget') and hasattr(self.vtk_widget, 'cleanup'):
                self.vtk_widget.cleanup()
        except Exception:
            pass
        try:
            self.vtk_widget.close()
        except Exception:
            pass
        super().closeEvent(arg__1)


    def load_series(self, index):
        self.current_series = self.series_list[index.row()]
        self.choose_idx = index.row()
        self.slice_slider.setRange(0, max(len(self.current_series.slices) - 1, 0))
        self.slice_slider.setValue(0)
        self.update_slice(0)
        self.vtk_widget.img_ren.ResetCamera()

    def apply_preset(self):
        # Add extra common presets (proactive enhancement)
        if not self.current_series:
            return
        preset = self.preset_combo.currentText()
        window, level = None, None
        extra_presets = {
            'Chest': (1500, -500),
            'CTA': (700, 200),
            'PET': (4000, 0),
            'MR-T1': (600, 300),
            'MR-T2': (1500, 0)
        }
        if preset == 'From DICOM':
            # Use first slice values
            ds = self.current_series.slices[0]
            window, level = self._extract_wl(ds, auto_if_missing=True)
        elif preset == 'Auto':
            ds = self.current_series.slices[self.slice_slider.value()]
            window, level = self._auto_wl(ds)
        elif preset in extra_presets:
            window, level = extra_presets[preset]
        else:
            presets = {
                'Brain': (80, 40),
                'Lung': (1500, -600),
                'Mediastinum': (350, 35),
                'Abdomen': (400, 50),
                'Bone': (2000, 300),
                'Liver': (150, 75),
                'Soft Tissue': (400, 40)
            }
            window, level = presets.get(preset, (400, 40))
        if window is not None:
            self.window_spin.setValue(int(window))
        if level is not None:
            self.level_spin.setValue(int(level))
        self.apply_manual_window_level()

    def apply_manual_window_level(self):
        self._manual_window = self.window_spin.value()
        self._manual_level = self.level_spin.value()
        # Re-render current slice with new settings
        self.update_slice(self.slice_slider.value())

    def _extract_wl(self, ds, auto_if_missing=False):
        try:
            windows = np.array(getattr(ds, 'WindowWidth'))
            levels = np.array(getattr(ds, 'WindowCenter'))
            if windows.size > 1:
                window = float(windows[0])
                level = float(levels[0])
            else:
                window = float(windows)
                level = float(levels)
            return window, level
        except Exception:
            if auto_if_missing:
                return self._auto_wl(ds)
            return None, None

    def _auto_wl(self, ds):
        try:
            arr = self._get_pixel_array(ds)
            # Exclude padding values from statistics if present
            pad = getattr(ds, 'PixelPaddingValue', None)
            if pad is not None:
                arr_masked = arr[arr != float(pad)]
                if arr_masked.size > 0:
                    arr = arr_masked
            vmin = float(np.percentile(arr, 5))
            vmax = float(np.percentile(arr, 95))
            window = vmax - vmin
            level = (vmax + vmin) / 2.0
            if window <= 0:
                window = float(np.max(arr) - np.min(arr)) or 1
                level = (float(np.max(arr)) + float(np.min(arr))) / 2.0
            return window, level
        except Exception:
            return 400, 40

    def _get_pixel_array(self, ds):
        # Ensure pixel data is available; if header-only, re-read
        try:
            has_pixel = hasattr(ds, 'PixelData') and ds.PixelData is not None
        except Exception:
            has_pixel = False
        if not has_pixel and hasattr(ds, '_filepath'):
            try:
                # Read full dataset with pixel data
                full = pydicom.dcmread(ds._filepath, force=True, stop_before_pixels=False)
                # Preserve frame index if any
                if hasattr(ds, '_frame_index'):
                    setattr(full, '_frame_index', getattr(ds, '_frame_index'))
                ds = full
            except Exception as e:
                raise e
        arr = ds.pixel_array
        # Multi-frame support
        if hasattr(ds, '_frame_index'):
            try:
                arr = arr[getattr(ds, '_frame_index')]
            except Exception:
                pass
        # Handle color images by converting to grayscale
        if arr.ndim == 3 and arr.shape[-1] in (3, 4):
            arr = arr[..., :3].astype(np.float32)
            arr = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
        # Apply rescale if present
        slope = getattr(ds, 'RescaleSlope', 1) or 1
        intercept = getattr(ds, 'RescaleIntercept', 0) or 0
        arr = arr.astype(np.float32) * float(slope) + float(intercept)
        # Handle MONOCHROME1 inversion (display white for low values)
        photometric = getattr(ds, 'PhotometricInterpretation', None)
        if photometric and str(photometric).upper() == 'MONOCHROME1':
            amax = np.max(arr)
            amin = np.min(arr)
            arr = (amax + amin) - arr
        return arr

    def update_slice(self, value):
        if not self.current_series or value >= len(self.current_series.slices):
            return
        # Update slice label early
        try:
            self.slice_label.setText(f"Slice: {value + 1}/{len(self.current_series.slices)}")
        except Exception:
            pass
        ds = self.current_series.slices[value]
        try:
            array = self._get_pixel_array(ds)
        except Exception as e:
            print(f"Failed to read pixel data for slice {value}: {e}")
            return

        # Flip vertically for display consistency
        array = array[::-1, :]

        # Convert to VTK image
        image_data = vtk.vtkImageData()
        cols = getattr(ds, 'Columns', array.shape[1])
        rows = getattr(ds, 'Rows', array.shape[0])
        cols = int(cols)
        rows = int(rows)
        image_data.SetDimensions(cols, rows, 1)
        # Use pixel spacing if present
        try:
            spacing = getattr(ds, 'PixelSpacing', [1.0, 1.0])
            sx = float(spacing[0]) if len(spacing) > 0 else 1.0
            sy = float(spacing[1]) if len(spacing) > 1 else 1.0
        except Exception:
            sx, sy = 1.0, 1.0
        image_data.SetSpacing(sx, sy, 1.0)
        image_data.SetOrigin(0.0, 0.0, 0.0)
        image_data.SetExtent(0, cols - 1, 0, rows - 1, 0, 0)

        vtk_data = npys.numpy_to_vtk(array.ravel(order='C'), deep=True, array_type=vtk.VTK_FLOAT)
        image_data.GetPointData().SetScalars(vtk_data)

        # Determine window/level
        if self._manual_window is not None and self._manual_level is not None:
            window = self._manual_window
            level = self._manual_level
        else:
            w, l = self._extract_wl(ds, auto_if_missing=True)
            window = w if w is not None else 400
            level = l if l is not None else 40
            self.window_spin.setValue(int(window))
            self.level_spin.setValue(int(level))

        self.vtk_widget.slice_actor.GetProperty().SetColorWindow(float(window))
        self.vtk_widget.slice_actor.GetProperty().SetColorLevel(float(level))

        self.vtk_widget.slice_mapper.SetInputData(image_data)
        self.vtk_widget.win.Render()

    def get_plane_orientation(self, orientation):
        if not orientation or len(orientation) < 6:
            return "Axial"
        row_vec = np.array(orientation[:3])
        col_vec = np.array(orientation[3:6])
        normal_vec = np.cross(row_vec, col_vec)
        abs_normal = np.abs(normal_vec)
        max_axis = np.argmax(abs_normal)
        if max_axis == 2:
            return "Axial"
        elif max_axis == 0:
            return "Sagittal"
        elif max_axis == 1:
            return "Coronal"
        return "Oblique"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.dicom_series = None

    def init_ui(self):
        self.setWindowTitle("DICOM Viewer")
        self.setGeometry(100, 100, 800, 600)

        open_btn = QPushButton("Open DICOM Folder", self)
        open_btn.clicked.connect(self.open_dicom)

        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(open_btn)
        layout.addWidget(self.vtk_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_dicom(self):
        path = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not path:
            return
        self.loader = DicomLoader(path)
        self.loader_thread = QThread()
        self.loader.moveToThread(self.loader_thread)
        # Progress dialog
        self.progress_dialog = QProgressDialog("Loading DICOM...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setValue(0)
        self.loader.progress.connect(self.progress_dialog.setValue)
        self.progress_dialog.canceled.connect(lambda: self.loader_thread.requestInterruption())
        self.loader_thread.started.connect(self.loader.run)
        self.loader.finished.connect(self.show_preview)
        self.loader.finished.connect(self.loader_thread.quit)
        self.loader.finished.connect(self.progress_dialog.close)
        self.loader_thread.start()
        self.progress_dialog.show()

    def show_preview(self, series_list):
        preview = PreviewWindow(series_list, self)
        if preview.exec() == QDialog.Accepted:
            self.dicom_series = preview.current_series
            print("Selected series:", self.dicom_series.name)

