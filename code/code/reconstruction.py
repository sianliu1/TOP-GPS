import numpy as np
from vtkmodules.vtkCommonDataModel import vtkPolyData

from nnunet.inference.predict_simple import predict_itk_data
from nnunet.training.network_training.custom_trainers import nnUNetTrainerV2_ep4000_nomirror
import vtkmodules.all as vtk
from vtkmodules.util import numpy_support as npy
import SimpleITK as sitk
import json



def rec_all(data_itk,model_name:str):


    seg_data = predict_itk_data(data_itk,model_name)

    return seg_data

class CusActor(vtk.vtkActor):
    def __init__(self):
        super(CusActor, self).__init__()

        self.label_name = None

class DataInfo:
    def __init__(self):
        self.spacing = None
        self.dim = None
        self.origin = None

class RecData:
    def __init__(self):
        self.name = "None"
        self.mask = None
        self.actor = None
        self.color = [1,0,0]


class MeshProcess:

    @staticmethod
    def mesh_smooth(polydata:vtk.vtkPolyData, data_type:int = 2):
        if 1 == data_type:
            normal_filter = vtk.vtkPolyDataNormals()
            normal_filter.SetInputData(polydata)
            normal_filter.Update()

            return normal_filter.GetOutput()
        elif 2 == data_type:
            smooth_filter = vtk.vtkWindowedSincPolyDataFilter()
            smooth_filter.SetInputData(polydata)
            smooth_filter.BoundarySmoothingOn()
            smooth_filter.SetNumberOfIterations(50)
            smooth_filter.SetPassBand(0.001)

            dec_filter = vtk.vtkDecimatePro()
            dec_filter.SetInputConnection(smooth_filter.GetOutputPort())
            dec_filter.SetTargetReduction(0.3)
            dec_filter.PreserveTopologyOn()

            smooth2_filter = vtk.vtkWindowedSincPolyDataFilter()
            smooth2_filter.SetInputConnection(dec_filter.GetOutputPort())
            smooth2_filter.BoundarySmoothingOn()
            smooth2_filter.SetNumberOfIterations(20)
            smooth2_filter.SetPassBand(0.001)


            normal_filter = vtk.vtkPolyDataNormals()
            normal_filter.SetInputConnection(smooth2_filter.GetOutputPort())
            normal_filter.Update()

            return normal_filter.GetOutput()

        elif 3 == data_type:

            smooth_filter = vtk.vtkWindowedSincPolyDataFilter()
            smooth_filter.SetInputData(polydata)
            smooth_filter.BoundarySmoothingOn()
            smooth_filter.SetNumberOfIterations(20)
            smooth_filter.SetPassBand(0.005)

            dec_filter = vtk.vtkDecimatePro()
            dec_filter.SetInputConnection(smooth_filter.GetOutputPort())
            dec_filter.SetTargetReduction(0.22)
            dec_filter.PreserveTopologyOn()


            smooth2_filter = vtk.vtkWindowedSincPolyDataFilter()
            smooth2_filter.SetInputConnection(dec_filter.GetOutputPort())
            smooth2_filter.BoundarySmoothingOn()
            smooth2_filter.SetNumberOfIterations(10)
            smooth2_filter.SetPassBand(0.005)

            dec2_filter = vtk.vtkDecimatePro()
            dec2_filter.SetInputConnection(smooth2_filter.GetOutputPort())
            dec2_filter.SetTargetReduction(0.1)
            dec2_filter.PreserveTopologyOn()

            normal_filter = vtk.vtkPolyDataNormals()
            normal_filter.SetInputConnection(dec2_filter.GetOutputPort())
            normal_filter.Update()

            return normal_filter.GetOutput()

        else:
            raise ValueError("data_type should be 1, 2 or 3")

    @staticmethod
    def npy2polydata(seg_data:np.ndarray, value:int = 1):
        tmp_img = vtk.vtkImageData()
        tmp_img.SetDimensions(seg_data.shape)
        tmp_img.SetS

        mc = vtk.vtkDiscreteMarchingCubes()
        mc.SetInputData(seg_data)
        mc.SetValue(0, value)
        mc.Update()

        return mc.GetOutput()
    @staticmethod
    def itk2polydata(itk_data, value:int = 1):

        tmp_npy = sitk.GetArrayFromImage(itk_data)

        tmp_img = vtk.vtkImageData()
        tmp_img.SetDimensions(itk_data.GetSize())
        tmp_img.SetSpacing(itk_data.GetSpacing())
        tmp_img.SetOrigin(itk_data.GetOrigin())
        tmp_img.GetPointData().SetScalars(npy.numpy_to_vtk(tmp_npy.ravel(),deep=True))


        mc = vtk.vtkDiscreteMarchingCubes()
        mc.SetInputData(tmp_img)
        mc.SetValue(0, value)
        mc.Update()

        return mc.GetOutput()

    @staticmethod
    def polydata2act(polydata:vtk.vtkPolyData):
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        act = CusActor()
        act.SetMapper(mapper)

        return act
