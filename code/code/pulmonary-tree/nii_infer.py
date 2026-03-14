import json
import os
import numpy as np
# from VesselVio-main.library import (
#     image_processing as ImProc,
#     volume_processing as VolProc,
#     graph_processing as GProc,
#     graph_io as GIO,
#     feature_extraction as FeatExt,
#     input_classes as IC,
# )
import torch

from VesselVio.library import (
    image_processing as ImProc,
    volume_processing as VolProc,
    graph_processing as GProc,
    graph_io as GIO,
    feature_extraction as FeatExt,
    input_classes as IC,
)
from model.utilities import pc_normalize, load_tensors_from_fold
from model.pg_model import IPGN
import SimpleITK as sitk

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#路径参数
file_path = r"data\input\tube2.nii.gz"
network_config_file = r"specs\network_specs.json"
IPGN_path = r"ckp\airway\weights\data"
# max_node 支气管 519 动静脉 1813  其它 1691
max_node = 1813
num_class = 19
verbose = True  # 是否打印详细信息
out_path = file_path.split('\\')[-1]
#首先计算血管特征
# 1. 分割结果读取
# 加载分割结果
# volume, image_shape = ImProc.load_volume(file_path, verbose=verbose)
volume = sitk.GetArrayFromImage(sitk.ReadImage(file_path))
image_shape = volume.shape

# 2. 体积预处理
volume_crop, point_minima = VolProc.volume_prep(volume)
print(f'crop_shape:{volume_crop.shape}')
# 3. 骨架化（中心线提取）
points = VolProc.skeletonize(volume_crop, verbose=verbose)

# 4. 半径计算
resolution = np.array([1, 1, 1])  # 分辨率，可以根据实际情况调整
skeleton_radii, vis_radii = VolProc.radii_calc_input(
    volume_crop, points, resolution, gen_vis_radii=True, verbose=verbose
)

# 5. 图结构构建
volume_shape = volume_crop.shape
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

# # 8. 图保存
# results_folder = gen_options.results_folder
# GIO.save_graph(graph, filename, results_folder, verbose=verbose)

graph_nodes = np.array( graph.vs['v_coords'])

graph_edges = graph.get_edgelist()

### 开始分段流程

with open(network_config_file) as network_specs_file:
    network_specs = network_specs_file.read()
    network_specs = json.loads(network_specs)


full_inference_pts = np.transpose(np.array(np.where(volume > 0)), (1, 0))
maxs = np.amax(full_inference_pts, axis=0)
mins = np.amin(full_inference_pts, axis=0)
full_inference_pts_normed = torch.stack([torch.from_numpy((full_inference_pts - mins) / (maxs - mins))], dim=0)

# 提取所有节点的坐标
all_nodes = np.array(graph_nodes)

nodes_maxs = np.amax(all_nodes, axis=0)
nodes_mins = np.amin(all_nodes, axis=0)

all_nodes = (np.array(all_nodes) - nodes_mins) / (nodes_maxs - nodes_mins)

# 提取所有边的索引
all_edges = graph_edges

# 转换为张量
all_nodes = torch.tensor(all_nodes, dtype=torch.float32)
all_edges = torch.tensor(all_edges, dtype=torch.long)

ext_edges = torch.clone(all_edges)
ext_edges = ext_edges[:,[1,0]]

new_edges = torch.vstack([all_edges, ext_edges])

# new_all_edges = torch.hstack((all_edges,all_edges))
new_all_edges = new_edges.to(device).t()

# 填充节点特征
node_pad = max_node
all_nodes_pad = torch.ones((node_pad, 3)) * (-10)
all_nodes_pad[:all_nodes.shape[0]] = all_nodes

# 提取点云数据
points = np.transpose(np.nonzero(volume))  # (num_points, 3)
targets = volume[points[:, 0], points[:, 1], points[:, 2]] - 1
perm = np.random.permutation(points.shape[0])
points = points[perm]
targets = targets[perm]
full_points = points[:6000]

full_points = (full_points-mins)/(maxs-mins)  # 归一化处理


# 转换为张量
full_points = torch.stack([ torch.from_numpy(full_points)],dim=0).float().to(device)

B,N,C = full_points.shape
nodes = all_nodes_pad.view(B,-1,C).float().to(device)

# 加载模型
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IPGN = IPGN(network_specs, num_class=num_class, max_node=max_node, device=device).to(device)
IPGN.point_graph_network.implicit_inference_mode()

tensors = load_tensors_from_fold(IPGN_path)
state_dic = IPGN.state_dict()
keys = list(state_dic.keys())

for i,key in enumerate(keys):
    if i < len(tensors) :
        tmp_shape = state_dic[key].shape
        if len(tmp_shape)>0:
            state_dic[key] = tensors[i].reshape(tmp_shape)
    else:
        break
IPGN.load_state_dict(state_dic)

print('Model loaded')
IPGN.point_graph_network.implicit_inference_mode()
IPGN.eval()

# 推理
with torch.no_grad():
    predictions = IPGN(full_inference_pts_normed, full_points, nodes, new_all_edges,full_voxel = True)+1

# sample_img = np.zeros_like(volume, dtype=np.float32)
# c_pts = pts.cpu().numpy().astype(np.int32)
#
# for smpple_ind in range(c_pts.shape[1]):
#     sample_img[c_pts[0, smpple_ind, 0], c_pts[0, smpple_ind, 1], c_pts[0, smpple_ind, 2]] = 1
#
# sitk.WriteImage(sitk.GetImageFromArray(sample_img), r"tube3_sample.nii.gz")
#
# with open('tmp_nodes', 'w') as f:
#     for node in nodes[0]:
#         f.write(f"{node[0]}, {node[1]}, {node[2]}\n")
#
# with open('tmp_edges', 'w') as f:
#     for edge in ei.t():
#         f.write(f"{edge[0]}, {edge[1]}\n")


# 输出nii.gz文件
output_volume = np.zeros_like(volume, dtype=np.float32)

for ind in range(full_inference_pts.shape[0]):
    output_volume[full_inference_pts[ind, 0], full_inference_pts[ind, 1], full_inference_pts[ind, 2]] = predictions[ind]


sitk.WriteImage(sitk.GetImageFromArray(output_volume), out_path)
