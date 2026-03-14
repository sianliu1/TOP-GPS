import os
import json
import time

import numpy as np
import SimpleITK as sitk
import torch
import argparse

from VesselVio.library import (
    image_processing as ImProc,
    volume_processing as VolProc,
    graph_processing as GProc,
    graph_io as GIO,
    feature_extraction as FeatExt,
    input_classes as IC,
)
from model.utilities import load_tensors_from_fold
from model.pg_model import IPGN


def preprocess_volume(file_path, resolution, prune_length, filter_length, verbose=True):
    volume = sitk.GetArrayFromImage(sitk.ReadImage(file_path))
    image_shape = volume.shape

    volume_crop, point_minima = VolProc.volume_prep(volume)
    points = VolProc.skeletonize(volume_crop, verbose=verbose)
    skeleton_radii, vis_radii = VolProc.radii_calc_input(volume_crop, points, resolution, gen_vis_radii=True, verbose=verbose)
    graph = GProc.create_graph(volume_crop.shape, skeleton_radii, vis_radii, points, point_minima, verbose=verbose)
    GProc.prune_input(graph, prune_length, resolution, verbose=verbose)
    GProc.filter_input(graph, filter_length, resolution, verbose=verbose)

    filename = os.path.basename(file_path)
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

    FeatExt.feature_input(
        graph, resolution, filename, image_dim=gen_options.image_dimensions,
        image_shape=volume.shape, roi_name="None", roi_volume="NA",
        save_seg_results=gen_options.save_seg_results, reduce_graph=True, verbose=verbose
    )

    return volume, graph


def normalize_points(points):
    mins = np.amin(points, axis=0)
    maxs = np.amax(points, axis=0)
    return (points - mins) / (maxs - mins), mins, maxs


def prepare_graph_data(graph, max_node, device):
    nodes = np.array(graph.vs['v_coords'])
    edges = np.array(graph.get_edgelist())

    norm_nodes, nodes_min, nodes_max = normalize_points(nodes)
    node_tensor = torch.ones((max_node, 3), dtype=torch.float32) * -10
    node_tensor[:len(norm_nodes)] = torch.tensor(norm_nodes, dtype=torch.float32)

    edge_tensor = torch.tensor(edges, dtype=torch.long)
    full_edges = torch.vstack([edge_tensor, edge_tensor[:, [1, 0]]]).T.to(device)

    return node_tensor.unsqueeze(0).to(device), full_edges, (nodes_min, nodes_max)


def prepare_input_points(volume, num_samples=6000):
    points = np.transpose(np.nonzero(volume))  # (N, 3)
    if len(points) > num_samples:
        points = points[np.random.permutation(len(points))[:num_samples]]
    norm_points, mins, maxs = normalize_points(points)
    return torch.tensor(norm_points).unsqueeze(0).float(), torch.tensor(points), (mins, maxs)


def load_model(network_config_file, model_weights_folder, num_class, max_node, device):
    with open(network_config_file) as f:
        net_cfg = json.load(f)
    model = IPGN(net_cfg, num_class=num_class, max_node=max_node, device=device).to(device)
    model.point_graph_network.implicit_inference_mode()

    # weights = load_tensors_from_fold(model_weights_folder)
    # state_dict = model.state_dict()
    # for i, k in enumerate(state_dict.keys()):
    #     if i < len(weights):
    #         tmp_shape = state_dict[k].shape
    #         if len(tmp_shape)>0:
    #             state_dict[k] = weights[i].reshape(state_dict[k].shape)
    #     else:
    #         break
    # model.load_state_dict(state_dict)
    # model.eval()
    weights = torch.load(model_weights_folder)
    model.load_state_dict(weights)
    model.eval()

    # torch.save(model.state_dict(),"airway_weights.pth")

    return model


def run_inference(
    model, volume, graph, max_node, resolution, device,
    num_class, full_voxel=True, verbose=True
):
    graph_nodes, edge_tensor, _ = prepare_graph_data(graph, max_node, device)
    input_points, raw_points, (min_pt, max_pt) = prepare_input_points(volume)

    # Normalize the full inference space (nonzero)
    inference_pts = np.transpose(np.array(np.where(volume > 0)), (1, 0))
    inference_pts_norm, _, _ = normalize_points(inference_pts)
    inference_pts_tensor = torch.tensor(inference_pts_norm).unsqueeze(0).float().to(device)

    with torch.no_grad():
        pred = model(inference_pts_tensor, input_points.to(device), graph_nodes, edge_tensor, full_voxel=full_voxel) + 1

    return pred, inference_pts


def save_prediction(predictions, inference_pts, volume_shape, out_path):
    output_volume = np.zeros(volume_shape, dtype=np.float32)
    for i in range(len(inference_pts)):
        x, y, z = inference_pts[i]
        output_volume[x, y, z] = predictions[i]
    sitk.WriteImage(sitk.GetImageFromArray(output_volume), out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",'--input_segment',help="Must input segment data",required=True)
    parser.add_argument("-t",'--type',help="input the data type,0:airway 1:artery 2:vein",default=0)
    parser.add_argument("-o",'--output_folder',help="please input output folder path",required=True)

    args=parser.parse_args()
    file_path = args.input_segment
    data_type = int(args.type)
    out_folder = args.output_folder

    # ================= CONFIGURATION ==================
    network_config_file = r"network\network_specs.json"
    model_weights_folder = r"network"
    model_path = None
    max_node = 1813

    if 0 == data_type:
        model_path = os.path.join(model_weights_folder,"airway_weigths.pth")
        max_node = 519
    elif 1== data_type:
        model_path = os.path.join(model_weights_folder,"artery_weigths.pth")
    elif 2 == data_type:
        model_path = os.path.join(model_weights_folder,"vein_weigths.pth")

    output_path = os.path.join(out_folder,"result.nii")

    resolution = np.array([1, 1, 1])
    prune_length = 5
    filter_length = 10

    num_class = 19
    verbose = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t1 = time.time()
    # ================= RUN PIPELINE ===================
    print("[INFO] Starting preprocessing...")
    volume, graph = preprocess_volume(file_path, resolution, prune_length, filter_length, verbose)
    t2 = time.time()
    print(f'volume shape:{volume.shape}')
    print("[INFO] Loading model...")
    model = load_model(network_config_file, model_path, num_class, max_node, device)
    t3 = time.time()
    print("[INFO] Running inference...")
    predictions, inference_pts = run_inference(
        model, volume, graph, max_node, resolution, device, num_class, full_voxel=True, verbose=verbose
    )
    t4 = time.time()
    print(f'Predictions shape: {predictions.shape}')
    print("[INFO] Saving result to:", output_path)
    save_prediction(predictions, inference_pts, volume.shape, output_path)

    print("[DONE] Inference pipeline completed.")

    print(f'preproc:{t2-t1},load model:{t3-t2}, inference:{t4-t3}')