import json
import os
import numpy as np
import torch
import networkx as nx
from model.utilities import pc_normalize, load_tensors_from_fold
from model.pg_model import IPGN
import SimpleITK as sitk

device = torch.device("cuda")
def load_and_preprocess_data(graph_file, volume_file, max_node=519):
    # 读取图结构数据
    g = nx.read_graphml(graph_file)

    # 读取体积数据
    # vol = np.load(volume_file)
    # volume = vol[vol.files[0]]
    volume = sitk.GetArrayFromImage(sitk.ReadImage(volume_file))

    full_inference_pts = np.transpose(np.array(np.where(volume > 0)), (1, 0))
    maxs = np.amax(full_inference_pts, axis=0)
    mins = np.amin(full_inference_pts, axis=0)
    full_inference_pts_normed = torch.stack([torch.from_numpy((full_inference_pts - mins) / (maxs - mins))], dim=0)

    # 提取所有节点的坐标
    all_nodes = []
    for node in g.nodes(data=True):
        node_coor = [float(node[1]['Z']), float(node[1]['Y']), float(node[1]['X'])]
        all_nodes.append(node_coor)

    nodes_maxs = np.amax(all_nodes, axis=0)
    nodes_mins = np.amin(all_nodes, axis=0)

    all_nodes = (np.array(all_nodes) - nodes_mins) / (nodes_maxs - nodes_mins)

    # 提取所有边的索引
    all_edges = []
    for edge in g.edges():
        all_edges.append([int(edge[0][1:]), int(edge[1][1:])])



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


    return volume,full_inference_pts,full_inference_pts_normed, full_points, nodes, new_all_edges


# 示例使用
graph_file = r"results\Graphs\tube3.nii.graphml"
volume_file = r"tmpdata\tube3.nii.gz"
max_node = 519

network_config_file = r"specs\network_specs.json"
with open(network_config_file) as network_specs_file:
    network_specs = network_specs_file.read()
    network_specs = json.loads(network_specs)
IPGN_path = r"ckp\airway\weights\data"

# 加载和预处理数据
volume,full_inference_pts,full_inference_pts_normed, pts, nodes, ei = load_and_preprocess_data(graph_file, volume_file, max_node)

# 加载模型
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IPGN = IPGN(network_specs, num_class=19, max_node=max_node, device=device).to(device)
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
    predictions = IPGN(full_inference_pts_normed, pts, nodes, ei,full_voxel = True)+1

sample_img = np.zeros_like(volume, dtype=np.float32)
c_pts = pts.cpu().numpy().astype(np.int32)

for smpple_ind in range(c_pts.shape[1]):
    sample_img[c_pts[0, smpple_ind, 0], c_pts[0, smpple_ind, 1], c_pts[0, smpple_ind, 2]] = 1

sitk.WriteImage(sitk.GetImageFromArray(sample_img), r"tube3_sample.nii.gz")

with open('tmp_nodes', 'w') as f:
    for node in nodes[0]:
        f.write(f"{node[0]}, {node[1]}, {node[2]}\n")

with open('tmp_edges', 'w') as f:
    for edge in ei.t():
        f.write(f"{edge[0]}, {edge[1]}\n")


# 输出nii.gz文件
output_volume = np.zeros_like(volume, dtype=np.float32)

for ind in range(full_inference_pts.shape[0]):
    output_volume[full_inference_pts[ind, 0], full_inference_pts[ind, 1], full_inference_pts[ind, 2]] = predictions[ind]


sitk.WriteImage(sitk.GetImageFromArray(output_volume), r"tube3_pred.nii.gz")
