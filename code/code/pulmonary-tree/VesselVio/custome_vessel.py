import os
import numpy as np
from library import (
    image_processing as ImProc,
    volume_processing as VolProc,
    graph_processing as GProc,
    graph_io as GIO,
    feature_extraction as FeatExt,
    input_classes as IC,
)

# 1. 分割结果读取
file_path = r"E:\DataProcess\lungtest\segdata\tube3.nii"
verbose = True  # 是否打印详细信息

# 加载分割结果
volume, image_shape = ImProc.load_volume(file_path, verbose=verbose)

# 2. 体积预处理
volume, point_minima = VolProc.volume_prep(volume)

# 3. 骨架化（中心线提取）
points = VolProc.skeletonize(volume, verbose=verbose)

# 4. 半径计算
resolution = np.array([1, 1, 1])  # 分辨率，可以根据实际情况调整
skeleton_radii, vis_radii = VolProc.radii_calc_input(
    volume, points, resolution, gen_vis_radii=True, verbose=verbose
)

# 5. 图结构构建
volume_shape = volume.shape
graph = GProc.create_graph(
    volume_shape, skeleton_radii, vis_radii, points, point_minima, verbose=verbose
)

# 6. 图优化
# 设置剪枝和过滤的参数
prune_length = 5  # 剪枝长度阈值
filter_length = 10  # 过滤长度阈值

# 剪枝：去除短的端点段
GProc.prune_input(graph, prune_length, resolution, verbose=verbose)

# 过滤：去除短的孤立段
GProc.filter_input(graph, filter_length, resolution, verbose=verbose)

# 7. 特征提取
filename = os.path.basename(file_path)  # 文件名
roi_name = "None"  # 区域名称，可以根据需要设置
roi_volume = "NA"  # 区域体积，可以根据需要设置
gen_options = IC.AnalysisOptions(
    results_folder="results",
    resolution=resolution,
    prune_length=prune_length,
    filter_length=filter_length,
    max_radius=150,
    save_segment_results=True,
    save_graph=True,
    image_dimensions=3,
)

# 提取特征
result, seg_results = FeatExt.feature_input(
    graph,
    resolution,
    filename,
    image_dim=gen_options.image_dimensions,
    image_shape=image_shape,
    roi_name=roi_name,
    roi_volume=roi_volume,
    save_seg_results=gen_options.save_seg_results,
    reduce_graph=True,
    verbose=verbose,
)

# 8. 图保存
results_folder = gen_options.results_folder
GIO.save_graph(graph, filename, results_folder, verbose=verbose)