import vtkmodules.all as vtk
from PySide6.QtWidgets import QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk
from PySide6.QtCore import Qt, QEvent, Signal


class SliceWin(QVTKRenderWindowInteractor):
    def __init__(self, parent=None):
        super(SliceWin, self).__init__(parent)

        self.iren = self.GetRenderWindow().GetInteractor()
        self.win = self.GetRenderWindow()


        self.viewer = vtk.vtkImageViewer2()
        self.viewer.SetRenderWindow(self.win)
        self.viewer.SetupInteractor(self.win.GetInteractor())
        self.viewer.SetSliceOrientationToXY()
        self.viewer.SetSlice(0)
        self.viewer.SetColorWindow(1200)
        self.viewer.SetColorLevel(-400)


        self.ren = self.win.GetRenderers().GetFirstRenderer()

        self.contour_ren = vtk.vtkRenderer()

        self.win.AddRenderer(self.contour_ren)
        self.ren.SetLayer(0)
        self.contour_ren.SetLayer(1)


        tmp_mapper = vtk.vtkPolyDataMapper()
        tmp_actor = vtk.vtkActor()
        tmp_actor.SetMapper(tmp_mapper)
        self.contour_ren.AddActor(tmp_actor)
        self.tmp_actor = tmp_actor


        # self.iren.Initialize()
class SliceWin2(QVTKRenderWindowInteractor):
    def __init__(self, parent=None):
        super(SliceWin2, self).__init__(parent)

        self.win = self.GetRenderWindow()
        # self.win.SetNumberOfLayers(2)

        # 设置 vtkImageSliceMapper
        slice_mapper = vtk.vtkImageSliceMapper()
        slice_mapper.SetSliceFacesCamera(True)
        slice_mapper.SetSliceAtFocalPoint(True)


        # 创建 vtkImageSlice
        slice_actor = vtk.vtkImageSlice()
        slice_actor.SetMapper(slice_mapper)
        slice_actor.GetProperty().SetColorWindow(1200)
        slice_actor.GetProperty().SetColorLevel(-400)
        slice_actor.SetPickable(0)
        self.slice_mapper = slice_mapper

        # 创建图像渲染器
        self.img_ren = vtk.vtkRenderer()
        self.img_ren.AddActor(slice_actor)
        self.img_ren.SetLayer(0)  # 设置图像渲染器的层次
        self.img_ren.SetInteractive(0)

        self.win.AddRenderer(self.img_ren)

        # 创建模型渲染器
        model_mapper = vtk.vtkPolyDataMapper()

        # # 创建一个简单的模型源，例如球体
        # sphere_source = vtk.vtkSphereSource()
        # sphere_source.SetRadius(50)
        # sphere_source.SetCenter(0, 0, 0)
        #
        # sphere_source.Update()  # 确保更新数据
        # model_mapper.SetInputData(sphere_source.GetOutput())

        model_actor = vtk.vtkActor()
        model_actor.SetMapper(model_mapper)
        model_actor.GetProperty().SetColor(1, 0, 0)  # 设置模型颜色
        model_actor.GetProperty().SetDiffuse(1)
        model_actor.GetProperty().SetSpecular(0)
        self.model_actor = model_actor

        self.img_ren.AddActor(model_actor)

        # self.model_ren = vtk.vtkRenderer()
        # self.model_ren.AddActor(model_actor)
        # self.model_ren.SetLayer(1)  # 设置模型渲染器的层次
        #
        # self.win.AddRenderer(self.model_ren)

        # 初始化渲染器和交互器
        self.iren = self.GetRenderWindow().GetInteractor()
        self.iren.Initialize()

        # 强制更新渲染窗口
        # self.win.Render()


class custom_InteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self):
        super(custom_InteractorStyle,self).__init__()

    def OnMouseWheelForward(self):
        pass
    def OnMouseWheelBackward(self):
        pass




class SliceWin3(QVTKRenderWindowInteractor):
    signal_wheel = Signal(int)
    def __init__(self, parent=None,win_type:str = "axial"):
        super(SliceWin3, self).__init__(parent)

        self.win = self.GetRenderWindow()
        # self.win.SetNumberOfLayers(2)

        tmp = vtk.vtkImageData()
        # 设置 vtkImageSliceMapper
        slice_mapper = vtk.vtkImageSliceMapper()
        slice_mapper.SetSliceFacesCamera(True)
        slice_mapper.SetSliceAtFocalPoint(True)
        slice_mapper.SetInputData(tmp)

        # 创建 vtkImageSlice
        slice_actor = vtk.vtkImageSlice()
        slice_actor.SetMapper(slice_mapper)
        slice_actor.GetProperty().SetColorWindow(1200)
        slice_actor.GetProperty().SetColorLevel(-400)
        slice_actor.SetPickable(0)
        self.slice_mapper = slice_mapper
        self.slice_actor = slice_actor

        # 创建图像渲染器
        self.img_ren = vtk.vtkRenderer()
        self.img_ren.AddActor(slice_actor)
        self.img_ren.SetLayer(0)  # 设置图像渲染器的层次
        self.img_ren.SetInteractive(0)



        self.win.AddRenderer(self.img_ren)

        label_mapper = vtk.vtkPolyDataMapper()
        # label_mapper.SetInputConnection(label_contour.GetOutputPort())
        label_mapper.SetScalarModeToUseCellData()

        label_actor = vtk.vtkActor()
        label_actor.SetMapper(label_mapper)
        label_actor.GetProperty().SetColor(1, 0, 0)
        label_actor.GetProperty().SetSpecular(0)
        label_actor.GetProperty().SetDiffuse(1)
        label_actor.GetProperty().SetLineWidth(2)

        self.label_mapper = label_mapper
        self.label_actors = []

        self.win_type = win_type

        # 初始化渲染器和交互器
        sty =vtk.vtkInteractorStyleImage()
        sty.AddObserver("MouseWheelForwardEvent", self.wheel_event)
        sty.AddObserver("MouseWheelBackwardEvent", self.wheel_event)

        self.iren = self.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(sty)


        self.iren.Initialize()

    def wheel_event(self, obj, event):
        if event == "MouseWheelForwardEvent":
            self.signal_wheel.emit(1)
        elif event == "MouseWheelBackwardEvent":
            self.signal_wheel.emit(-1)


    def update_pos(self):


        input_img = self.slice_mapper.GetInput()
        if input_img:
            tmp_pos = self.iren.GetEventPosition()
            # print(tmp_pos)
            cor = vtk.vtkCoordinate()
            cor.SetCoordinateSystemToDisplay()
            cor.SetValue(tmp_pos[0], tmp_pos[1], 0)
            tmp_pos = cor.GetComputedWorldValue(self.img_ren)

            # print(tmp_pos)

            extent = input_img.GetExtent()
            spacing = input_img.GetSpacing()
            origin = input_img.GetOrigin()
            dim = input_img.GetDimensions()
            pos = [0, 0]
            pos[0] = int((tmp_pos[0] - extent[0]) / spacing[0] + origin[0])
            pos[1] = int((tmp_pos[1] - extent[2]) / spacing[1] + origin[1])

            if pos[0] <0 or pos[0] >= dim[0]:
                pos[0] = -1
            if pos[1] <0 or pos[1] >= dim[1]:
                pos[1] = -1



            if self.win_type == "axial":
                if pos[1]>=0:
                    ind_value = [-1,dim[1] - pos[1],pos[0]]
                else:
                    ind_value = [-1,-1,pos[0]]

            elif self.win_type == "coronal":
                ind_value = [pos[1],-1,pos[0]]
            elif self.win_type == "sagittal":
                ind_value = [pos[1],pos[0],-1]
            else:
                ind_value = [-1,-1,-1]

            return ind_value

    def eventFilter(self, watched, event):

        if watched == self.iren:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_Space:
                    self.slice_actor.GetProperty().SetColorWindow(1200)
                    self.slice_actor.GetProperty().SetColorLevel(-400)
                    self.win.Render()
                    return True
        return False

    def cleanup(self):
        try:
            # Remove label actors
            for act in self.label_actors:
                try: self.img_ren.RemoveActor(act)
                except Exception: pass
            self.label_actors.clear()
        except Exception:
            pass
        _release_vtk_window(self)

def _release_vtk_window(qvtk):
    try:
        win = qvtk.GetRenderWindow()
        if win:
            try:
                rens = win.GetRenderers()
                if rens:
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
                if iren:
                    try: iren.RemoveAllObservers()
                    except Exception: pass
                    try: iren.Disable()
                    except Exception: pass
                    try: iren.SetRenderWindow(None)
                    except Exception: pass
            except Exception:
                pass
            try: win.SetAbortRender(True)
            except Exception: pass
            try: win.Finalize()
            except Exception: pass
            try: qvtk.SetRenderWindow(None)
            except Exception: pass
    except Exception:
        pass


class ThreeDimWin(QVTKRenderWindowInteractor):
    def __init__(self, parent=None):
        super(ThreeDimWin, self).__init__(parent)

        self.iren = self.GetRenderWindow().GetInteractor()
        self.win = self.GetRenderWindow()

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0,0,0)
        self.win.AddRenderer(self.ren)
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())


        self.iren.Initialize()
        # Do not start a blocking VTK event loop inside Qt
        # self.iren.Start()

    def cleanup(self):
        _release_vtk_window(self)
