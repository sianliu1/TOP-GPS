# Pulmonary-Tree

`pulmonary-tree/` is an independent submodule for pulmonary tree grading, designed for graph-based modeling and branch-level inference on bronchial, arterial, and venous tree structures. It can be used either as a standalone inference package or as an upstream grading engine invoked by the main application for watershed analysis.

From a task-definition perspective, this module does not target generic voxel-wise segmentation. Instead, it performs structured interpretation of an already segmented tree mask: given a binary airway or vessel volume, it reconstructs an explicit graph representation and predicts anatomically meaningful branch labels.

## Role in the Overall System

Within the full project pipeline, `pulmonary-tree/` sits between 3D anatomical reconstruction and downstream watershed mapping. Its responsibility is tree-structure semantic grading:

- Input: segmented bronchial, arterial, or venous volumes
- Intermediate representation: skeleton points, radius estimates, graph topology, and sampled point clouds
- Output: voxel-wise volumes with grading labels

In the main application, this module is currently invoked through [new_nii_infer.py](pulmonary-tree/new_nii_infer.py), and the bronchial grading result is further used for lobe-constrained watershed analysis.

## Method Overview

The overall processing chain can be summarized as follows:

1. Read a binary tree-structure volume.
2. Crop and preprocess the volume.
3. Extract the centerline through skeletonization.
4. Estimate local radii and construct a graph representation.
5. Prune short terminal branches and filter isolated short segments.
6. Build a joint representation consisting of graph nodes, edges, and sampled voxel points.
7. Run implicit inference with a point-graph fusion network.
8. Write the predicted labels back to the voxel space.

Compared with purely voxel-based convolutional pipelines, this module emphasizes explicit topological modeling of tree structures. Its core design combines:

- local geometric cues from point-cloud representations
- topological connectivity from graph representations
- dense voxel prediction from an implicit inference module

## Inference Pipeline

The main inference entry is [new_nii_infer.py](pulmonary-tree/new_nii_infer.py). In the current implementation, inference consists of the following stages.

### 1. Volume Preprocessing

The input is typically a binary NIfTI volume produced by an upstream segmentation stage. The module first reads the mask with `SimpleITK`, then relies on `VesselVio` utilities for:

- valid-region cropping
- skeleton extraction
- radius estimation
- graph construction
- graph pruning and short-branch filtering

The goal of this stage is to convert the raw voxel mask into an explicit structural representation suitable for topology-aware inference.

### 2. Joint Point-Graph Encoding

At the representation level, the module constructs two parallel inputs:

- a graph input defined by node coordinates and edge connectivity
- a point-cloud input sampled from nonzero voxels

Node coordinates and sampled points are normalized before entering the network. The number of graph nodes is padded to a fixed `max_node` size to match the network input interface. Different tasks use different node limits, for example:

- Airway: `Max_Node = 519`
- Artery: `Max_Node = 1813`
- Vein: `Max_Node = 1691`

These settings are defined in [dataset_specs_airway.json](pulmonary-tree/specs/dataset_specs_airway.json), [dataset_specs_artery.json](pulmonary-tree/specs/dataset_specs_artery.json), and [dataset_specs_vein.json](pulmonary-tree/specs/dataset_specs_vein.json).

### 3. Network Inference

The main model is `IPGN`, implemented in [pg_model.py](pulmonary-tree/model/pg_model.py). Based on [network_specs.json](pulmonary-tree/specs/network_specs.json), the architecture contains the following components:

- Graph Encoder: a GAT-based graph encoder
- Point Encoder: a point-cloud encoder
- Point-Graph Fusion: a fusion module for point and graph features
- Implicit Module: an implicit decoder for dense voxel prediction

This is therefore not a conventional single-path network. It is a hybrid point-graph framework that jointly models geometry and topology, which is particularly suitable for stable hierarchical prediction on pulmonary tree structures.

### 4. Label Projection Back to Volume Space

The network predicts labels for all target voxel locations, and those predictions are then projected back into the original volume coordinates to generate the final `result.nii`. In the upper-level application, this output can be used directly for pulmonary segment assignment, vascular grading visualization, or watershed analysis.

## Supported Tasks

The current implementation supports three tree-grading tasks, controlled by the `type` argument in [new_nii_infer.py](pulmonary-tree/new_nii_infer.py):

- `0`: airway
- `1`: artery
- `2`: vein

All three tasks share the same inference framework but use different weights and task-specific settings:

- `network/airway_weigths.pth`
- `network/artery_weigths.pth`
- `network/vein_weigths.pth`

The class count is configured as `19`, corresponding to the grading label system used by the model.

## Directory Structure

The most relevant files and folders for understanding this module are:

- [new_nii_infer.py](pulmonary-tree/new_nii_infer.py): current main inference entry, producing `result.nii`
- [nii_infer.py](pulmonary-tree/nii_infer.py): earlier inference experiment script
- [train_network.py](pulmonary-tree/train_network.py): training entry point
- [reconstruction_inference.py](pulmonary-tree/reconstruction_inference.py): reconstruction inference entry
- [specs](pulmonary-tree/specs): network, training, and dataset configuration files
- [network](pulmonary-tree/network): inference weights and network configuration
- [model](pulmonary-tree/model): model definitions, training logic, and inference implementation
- [VesselVio](pulmonary-tree/VesselVio): preprocessing, graph construction, and feature extraction code for tree structures

## Training and Configuration

The training entry is [train_network.py](pulmonary-tree/train_network.py). The current training workflow contains multiple stages:

- point encoder pretraining
- graph encoder pretraining
- point-graph fusion training
- implicit module training

The main configuration files are:

- [network_specs.json](pulmonary-tree/specs/network_specs.json)
- [train_inference_specs.json](pulmonary-tree/specs/train_inference_specs.json)
- task-specific dataset spec files under `specs/`

An example training command is:

```bash
python train_network.py -d dataset_specs_airway.json
```

## Inference Usage

An example inference command is:

```bash
python new_nii_infer.py -i input_mask.nii.gz -t 0 -o output_dir
```

Argument description:

- `-i`: input binary tree-structure volume
- `-t`: task type, where `0/1/2` correspond to airway, artery, and vein
- `-o`: output directory, where the result is saved as `result.nii`

When this module is used inside the main GUI application, it is typically not called manually from the command line. Instead, the upper-level application prepares the input volume, runs the inference process, and reads the generated result automatically.

## Dependencies

Based on the current implementation, the module mainly depends on the following components:

- Python 3.9
- PyTorch
- PyTorch Geometric
- SimpleITK
- NumPy
- VesselVio

The repository includes [requirments.txt](pulmonary-tree/requirments.txt) as an environment record. However, its content is closer to a snapshot of an existing runtime environment than to a strict minimal dependency specification. For environment reproduction, it should therefore be complemented with the actual imports used by the codebase.

## Relation to the Main Application

In the upper-level project, `pulmonary-tree/` acts as a structure-grading engine that can run independently or be invoked by the main application.

- In standalone mode, it performs tree-structure grading and outputs a labeled volume.
- In integrated mode, it serves as the upstream grading module for watershed analysis.

In short, this submodule is the core component for semantic grading and structured interpretation of pulmonary tree anatomy.