import SimpleITK
import vtkmodules.all as vtk
from vtkmodules.util import numpy_support as npys
from reconstruction import RecData

def update_slice(ct_itk, axis, slice_index, viewer, rec_datas=None):
    """显示截取的二维切片。
    方向与显示策略：
      - 数据数组 ct_data 形状 (z, y, x) => SimpleITK.GetArrayFromImage 默认。
      - axial: 取固定 z 得到 (y,x) 并做垂直翻转 ([::-1, :]) 来与 dcm_reader 预览保持一致。
      - coronal: 取固定 y 得到 (z,x)，不翻转。
      - sagittal: 取固定 x 得到 (z,y)，不翻转。
    spacing 映射：
      axial    -> (sx, sy, 1.0)
      coronal  -> (sx, sz, 1.0)  (行方向 z 对应 sz, 列方向 x 对应 sx)
      sagittal -> (sy, sz, 1.0)  (行方向 z 对应 sz, 列方向 y 对应 sy)
    标签掩膜在 axial 做同样的翻转，保证轮廓叠加位置正确。
    不再对其它平面做额外翻转，确保体素坐标与显示协调。
    """
    ct_data = SimpleITK.GetArrayFromImage(ct_itk)  # (z,y,x)
    spacing = ct_itk.GetSpacing()  # (sx, sy, sz)
    label_list = []

    if axis == 'axial':
        slice_data = ct_data[slice_index, :, :]              # (y,x)
        slice_data = slice_data[::-1, :]  # 垂直翻转匹配预览
        new_spacing = (spacing[0], spacing[1], 1.0)
        if rec_datas is not None:
            for tmp_rec in rec_datas:
                tmp_data = RecData()
                tmp_data.name = tmp_rec.name
                tmp_mask = tmp_rec.mask[slice_index, :, :]
                tmp_data.mask = tmp_mask[::-1, :]  # 同样翻转标签掩膜
                tmp_data.color = tmp_rec.color
                tmp_data.actor = tmp_rec.actor
                label_list.append(tmp_data)
    elif axis == 'coronal':
        slice_data = ct_data[:, slice_index, :]              # (z,x)
        new_spacing = (spacing[0], spacing[2], 1.0)
        if rec_datas is not None:
            for tmp_rec in rec_datas:
                tmp_data = RecData()
                tmp_data.name = tmp_rec.name
                tmp_data.mask = tmp_rec.mask[:, slice_index, :]
                tmp_data.color = tmp_rec.color
                tmp_data.actor = tmp_rec.actor
                label_list.append(tmp_data)
    elif axis == 'sagittal':
        slice_data = ct_data[:, :, slice_index]              # (z,y)
        # slice_data = slice_data[:, ::-1]  # 水平翻转匹配预览
        new_spacing = (spacing[1], spacing[2], 1.0)
        if rec_datas is not None:
            for tmp_rec in rec_datas:
                tmp_data = RecData()
                tmp_data.name = tmp_rec.name
                tmp_data.mask = tmp_rec.mask[:, :, slice_index]
                tmp_data.mask = tmp_data.mask
                tmp_data.color = tmp_rec.color
                tmp_data.actor = tmp_rec.actor
                label_list.append(tmp_data)
    else:
        return

    # 构造 vtkImageData
    rows, cols = slice_data.shape
    vtk_image = vtk.vtkImageData()
    vtk_image.SetDimensions(cols, rows, 1)
    vtk_image.SetSpacing(*new_spacing)

    vtk_data = npys.numpy_to_vtk(slice_data.astype('float32').ravel(), deep=True, array_type=vtk.VTK_FLOAT)
    vtk_image.GetPointData().SetScalars(vtk_data)

    viewer.slice_mapper.SetInputData(vtk_image)

    if rec_datas is not None and len(label_list) > 0:
        for tmp_act in viewer.label_actors:
            viewer.img_ren.RemoveActor(tmp_act)
        viewer.label_actors = []
        for tmp_data in label_list:
            label_image = vtk.vtkImageData()
            lr, lc = tmp_data.mask.shape
            label_image.SetDimensions(lc, lr, 1)
            label_image.SetSpacing(*new_spacing)
            label_image.GetPointData().SetScalars(
                npys.numpy_to_vtk(tmp_data.mask.astype('float32').ravel(), deep=True, array_type=vtk.VTK_FLOAT)
            )
            label_contour = vtk.vtkContourFilter()
            label_contour.SetInputData(label_image)
            label_contour.SetValue(0, 1)
            label_mapper = vtk.vtkPolyDataMapper()
            label_mapper.SetInputConnection(label_contour.GetOutputPort())
            label_mapper.SetScalarModeToUseCellData()
            label_actor = vtk.vtkActor()
            label_actor.SetMapper(label_mapper)
            label_actor.GetProperty().SetColor(tmp_data.color)
            viewer.img_ren.AddActor(label_actor)
            viewer.label_actors.append(label_actor)
