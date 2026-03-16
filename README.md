# Pulmonary Watershed Analysis Navigation System

This project is a pulmonary watershed analysis navigation system for chest CT, with the application entry located in [main.py](main.py). It integrates multi-planar image review, automatic anatomical reconstruction, tree-structure grading, and lobe-constrained watershed analysis into a single desktop workflow.

 It is a workflow-oriented analysis platform that combines anatomical reconstruction with structure-aware regional interpretation, allowing the user to move from raw CT data to interactive 2D/3D watershed navigation in one interface.

## Overview

The overall processing logic can be summarized as:

`CT input -> anatomical reconstruction -> tree grading -> watershed mapping -> interactive navigation`

The project is organized around three main layers:

1. User interface and workflow orchestration.
2. Automatic segmentation and 3D anatomical reconstruction.
3. Tree grading and watershed-oriented region mapping.

The main GUI is implemented in [presenter.py](presenter.py), while [main.py](main.py) is responsible for launching the application.

## System Architecture

```text
                    +----------------------+
                    |      main.py         |
                    |   Application Entry  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |    presenter.py      |
                    |   UI / Workflow Hub  |
                    +----+------------+----+
                         |            |
              +----------+            +------------------+
              |                                            |
              v                                            v
   +----------------------+                   +----------------------+
   |      nnunet/         |                   |   pulmonary-tree/    |
   | Segmentation Engine  |                   |  Tree Grading Engine |
   +----------+-----------+                   +----------+-----------+
              |                                            |
              v                                            v
   +----------------------+                   +----------------------+
   | 3D Reconstruction &  |                   | Branch / Segment     |
   | Anatomical Models    |                   | Classification       |
   +----------+-----------+                   +----------+-----------+
              |                                            |
              +--------------------+-----------------------+
                                   |
                                   v
                    +-------------------------------+
                    | Watershed Mapping in Main App |
                    | Lobe-constrained Region Parse |
                    +---------------+---------------+
                                    |
                                    v
                    +-------------------------------+
                    | 2D/3D Interactive Navigation  |
                    +-------------------------------+
```

## Main Components

### 1. Main Navigation Interface

The main window serves as the orchestration layer of the system. It provides:

- CT data loading
- three orthogonal slice viewers
- a 3D rendering window
- anatomical object visibility and opacity control
- automatic reconstruction entry
- watershed analysis entry

This layer is designed as an interactive navigation workspace rather than a static viewer. It allows synchronized inspection of slices, reconstructed surfaces, and watershed-derived segmental regions.

### 2. 3D Reconstruction

3D reconstruction is mainly supported by [nnunet](nnunet) and invoked through [reconstruction.py](reconstruction.py). In the current implementation, the reconstruction stage produces anatomical structures including:

- the five pulmonary lobes
- arteries
- veins
- bronchus

The resulting label volumes are converted into 3D polygonal models and rendered in the GUI. This stage provides the anatomical prior required for downstream grading and watershed mapping.

### 3. Tree Grading and Watershed Analysis

Tree grading is provided by the independent submodule [pulmonary-tree](pulmonary-tree). That module is responsible for graph-aware grading of airway and vascular tree structures.

In the main project, watershed analysis is built on top of the grading result rather than treated as a separate isolated step. In the current workflow, the application:

1. reconstructs the target lobe and bronchial structure
2. calls the tree-grading module
3. filters grading labels according to the selected lobe
4. maps lobe voxels to nearby graded branches
5. reconstructs and visualizes the resulting segment-level regions

For this reason, the project groups tree grading and watershed analysis together at the system level: the grading stage provides the structural semantics, and the watershed stage turns those semantics into lobe-constrained regional navigation.

## Repository Structure

The most relevant files and directories are:

- [main.py](main.py): application entry point
- [presenter.py](presenter.py): main window logic and workflow control
- [reconstruction.py](reconstruction.py): segmentation-to-surface reconstruction pipeline
- [config.json](config.json): anatomical labels, colors, smoothing types, and window presets
- [mainwindow.ui](mainwindow.ui): Qt UI definition
- [nnunet](nnunet): segmentation and reconstruction backend
- [pulmonary-tree](pulmonary-tree): independent tree-grading package

In short:

- [nnunet](nnunet) recovers anatomical structures from CT volumes.
- [pulmonary-tree](pulmonary-tree) assigns structural grading labels to tree-like anatomy.
- The main application fuses both outputs into an interactive watershed navigation workflow.

## Environment Setup

This repository is best treated as a Windows-based research prototype. The GUI stack, reconstruction pipeline, and grading components depend on multiple medical-imaging and deep-learning libraries, and the bundled dependency file is closer to a recorded working environment than to a strict minimal specification.

### Recommended Base Environment

- Windows
- Python 3.10 or 3.11 for the main GUI application
- CUDA-enabled PyTorch if GPU inference is required

### Install Dependencies

Create and activate a virtual environment first, then install the main dependencies.

Example with `conda`:

```bash
conda create -n watershed-nav python=3.11 -y
conda activate watershed-nav
```

Then install the project dependencies:

```bash
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu118
pip install -r requiment.txt
pip install -e .
```

Notes:

- [requiment.txt](requiment.txt) contains some machine-specific entries, including local editable paths and a local Torch wheel reference. These may need to be adjusted on another machine before installation.
- The repository already includes a local [setup.py](setup.py) for the bundled `nnunet` package. If needed, install it in editable mode with:


- If you plan to use the tree-grading submodule directly from source rather than via a packaged executable, also review [pulmonary-tree/README.md](pulmonary-tree/README.md) and its dependency notes.

### Core Runtime Libraries

The project relies primarily on:

- PySide6 for the GUI
- VTK for 2D/3D rendering
- SimpleITK, nibabel, and pydicom for medical-image IO
- PyTorch for model inference
- the local [nnunet](nnunet) package for segmentation-based reconstruction
- the local [pulmonary-tree](pulmonary-tree) package for tree grading

## Launching the Application

The main application is started from the repository root:

```bash
python main.py
```

After launch, the normal usage flow is:

1. load CT data
2. inspect the three orthogonal views
3. run automatic reconstruction
4. select a target lobe
5. trigger watershed analysis
6. inspect the generated 3D segmental or watershed regions

## Runtime Notes

- The GUI expects a valid [config.json](config.json) and the corresponding reconstruction labels defined there.
- Reconstruction and grading depend on local model files being available.
- The current codebase is oriented toward research use and reviewer demonstration rather than one-click general deployment.
- Some packaged or external inference components may be resolved differently across environments, especially if grading is executed through a compiled executable instead of direct Python invocation.

