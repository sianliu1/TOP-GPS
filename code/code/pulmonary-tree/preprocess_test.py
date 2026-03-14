import numpy as np


import SimpleITK as sitk
from scipy.ndimage import zoom
from mpl_toolkits.mplot3d.proj3d import transform


def read_npz(path: str):
    data = np.load(path)
    volume = data[data.files[0]]
    print(volume.shape)

    volume[volume>1] = 1

    img_np = volume.astype(np.float32)
    # Downsample the image by a factor of 0.25
    zoom_factors = (0.25, 0.25, 0.25)  # Downsample by 75%
    downsampled_volume = zoom(img_np, zoom_factors, order=2)  # Use linear interpolation

    downsampled_volume[downsampled_volume > 0.01] = 1
    downsampled_volume[downsampled_volume <= 0.01] = 0

    img_itk = sitk.GetImageFromArray(downsampled_volume.astype(np.int8))
    size = img_itk.GetSize()

    print(size)

    new_img_itk = sitk.Resample(img_itk,size)


    sitk.WriteImage(new_img_itk, 'test.nii.gz')

if __name__ == "__main__":
    tmp_path = r"data_npz\train\airway\sample_airway.npz"
    read_npz(tmp_path)