import numpy as np
import SimpleITK as sitk

def read_npz(path:str):
    data = np.load(path)
    volume = data[data.files[0]]
    print(volume.shape)

    sitk.WriteImage(sitk.GetImageFromArray(volume),'test.nii.gz')


#读取二值化模型文件

import torch
import os

def load_tensor_from_bin(path:str):
    with open(path,'rb') as f:
        data = f.read()

    tensor = torch.frombuffer(data,dtype=torch.float32)
    return tensor

def load_tensors_from_fold(path:str):
    tensors = []
    for tmp_f in os.listdir(path):
        tmp_path = os.path.join(path,tmp_f)
        tmp_tensor = load_tensor_from_bin(tmp_path)
        tensors.append(tmp_tensor)

    return tensors

if __name__ == "__main__":
    tmp_path = r"data_npz\train\airway\sample_airway.npz"
    read_npz(tmp_path)
