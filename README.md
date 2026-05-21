# Traffic Collision Detection System using YOLO11 + ByteTrack

## Overview

This project is a real-time intelligent traffic collision detection and analytics system built using:

* YOLO11 Large for vehicle detection
* ByteTrack for multi-object tracking
* Custom motion analytics engine
* Custom collision reasoning engine
* GPU acceleration using CUDA
* OpenCV-based visualization pipeline

The system processes traffic CCTV footage, detects vehicles, tracks them across frames, analyzes their trajectories and motion patterns, and intelligently determines whether a real collision has occurred.

The pipeline is optimized for:

* Dense traffic scenarios
* Close-up CCTV cameras
* Slow-speed impacts
* Rear-end collisions
* Side collisions
* Urban traffic monitoring

---

# Key Features

## Vehicle Detection

* Uses YOLO11 Large model
* High-quality bounding boxes
* Accurate vehicle localization
* GPU accelerated inference

## Multi-Object Tracking

* ByteTrack tracker integration
* Persistent object identities
* Stable trajectory tracking
* Motion continuity analysis

## Motion Analytics

* Speed estimation
* Acceleration estimation
* Direction estimation
* Sudden stop detection
* Motion consistency analysis
* Stability scoring

## Intelligent Collision Detection

* Relative motion analysis
* Adaptive distance reasoning
* Parallel traffic suppression
* Micro-impact detection
* Temporal collision persistence
* False-positive reduction

## Visualization & Outputs

* Output annotated video
* Collision alerts
* JSON collision logs
* Collision screenshots
* Real-time analytics display

---

# System Architecture

```text id="r1"
Input Video
    ↓
YOLO11 Vehicle Detection
    ↓
ByteTrack Tracking
    ↓
Trajectory Generation
    ↓
Motion Analytics
    ↓
Collision Reasoning Engine
    ↓
Event Confirmation
    ↓
Output Video + Logs + Screenshots
```

---

# Technologies Used

| Component        | Technology          |
| ---------------- | ------------------- |
| Detection        | YOLO11 Large        |
| Tracking         | ByteTrack           |
| Visualization    | OpenCV              |
| GPU Acceleration | CUDA                |
| Deep Learning    | PyTorch             |
| Analytics        | Custom Python Logic |
| Logging          | JSON                |
| Deployment       | Docker + NVIDIA GPU |

---

# Folder Structure

```text id="r2"
traffic-collision-project/
│
├── app/
│   ├── main.py
│   ├── detector.py
│   ├── tracker.py
│   ├── analytics.py
│   ├── event_detector.py
│   ├── confidence_engine.py
│   ├── collision_verifier.py
│   ├── alert_service.py
│   └── utils.py
│
├── configs/
│
├── models/
│   └── yolo11l.pt
│
├── outputs/
│   ├── videos/
│   ├── screenshots/
│   └── logs/
│
├── sample_videos/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# Complete Setup Guide

# 1. System Requirements

## Hardware

* NVIDIA GPU (Recommended)
* Minimum 8GB VRAM
* CUDA-supported GPU

## Software

* Ubuntu 20.04 / 22.04
* Docker
* NVIDIA Drivers
* NVIDIA Container Toolkit

---

# 2. Verify GPU

```bash id="r3"
nvidia-smi
```

Expected:

* GPU details visible
* CUDA version visible

---

# 3. Install Docker

```bash id="r4"
apt update

apt install -y docker.io
```

Enable Docker:

```bash id="r5"
systemctl start docker

systemctl enable docker
```

Verify:

```bash id="r6"
docker --version
```

---

# 4. Install NVIDIA Container Toolkit

```bash id="r7"
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt update

apt install -y nvidia-container-toolkit

nvidia-ctk runtime configure --runtime=docker

systemctl restart docker
```

---

# 5. Verify GPU inside Docker

```bash id="r8"
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

# 6. Create Project Folder

```bash id="r9"
mkdir -p /workspace/traffic-collision-project

cd /workspace/traffic-collision-project
```

---

# 7. Start DeepStream Container

```bash id="r10"
docker run -it --rm --gpus all \
--network=host \
-v $PWD:/workspace \
nvcr.io/nvidia/deepstream:7.0-gc-triton-devel
```

---

# 8. Install Python Dependencies

Inside container:

```bash id="r11"
pip install -r requirements.txt
```

---

# 9. Install PyTorch CUDA

```bash id="r12"
pip3 install torch torchvision torchaudio \
--index-url https://download.pytorch.org/whl/cu121
```

---

# 10. Install Ultralytics

```bash id="r13"
pip3 install ultralytics
```

---

# 11. Install ByteTrack Support

```bash id="r14"
pip3 install supervision
```

---

# 12. Verify Installations

```bash id="r15"
python3 -c "import cv2, torch, ultralytics, supervision; print('ALL OK')"
```

Expected:

```text id="r16"
ALL OK
```

---

# 13. Download YOLO11 Model

```bash id="r17"
mkdir -p /workspace/models

cd /workspace/models

wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt
```

---

# 14. Add Sample Video

Place traffic video here:

```text id="r18"
/workspace/sample_videos/crash.mp4
```

---

# 15. Run the Pipeline

```bash id="r19"
cd /workspace

python3 app/main.py
```

---

# Pipeline Working Explanation

# Step 1 — Vehicle Detection

YOLO11 Large processes every frame and detects:

* Cars
* Trucks
* Buses
* Motorcycles

Output:

* Bounding boxes
* Confidence scores
* Class labels

---

# Step 2 — Multi-Object Tracking

ByteTrack assigns persistent IDs to vehicles.

Example:

```text id="r20"
Car A → ID 1
Car B → ID 2
```

This enables:

* Trajectory generation
* Motion continuity
* Event persistence

---

# Step 3 — Trajectory Generation

Vehicle center positions are stored frame-by-frame.

Example:

```text id="r21"
[(120, 220), (125, 223), (132, 229)]
```

Used for:

* Speed analysis
* Motion analysis
* Direction analysis

---

# Step 4 — Motion Analytics

The analytics engine computes:

* Speed
* Acceleration
* Motion vectors
* Stability score
* Sudden stops

This improves:

* Real-world collision understanding
* False-positive suppression

---

# Step 5 — Collision Reasoning

The collision engine analyzes:

* Relative distance
* Relative motion
* Speed changes
* Sudden stops
* Direction conflicts
* Temporal persistence

The system distinguishes between:

* Actual collisions
* Normal traffic flow
* Dense traffic proximity
* Lane-following vehicles

---

# Step 6 — Event Confirmation

A collision is confirmed only if:

* Motion evidence is strong
* Collision persists across frames
* False-positive suppression passes
* Confidence threshold is met

---

# Step 7 — Output Generation

The system generates:

* Annotated output video
* Collision screenshots
* JSON event logs

---

# Outputs

# Output Video

```text id="r22"
outputs/videos/output.mp4
```

Contains:

* Bounding boxes
* Tracker IDs
* Vehicle direction
* Speed
* Collision alerts

---

# Collision Logs

```text id="r23"
outputs/logs/collision_log.json
```

Contains:

* Vehicle IDs
* Timestamp
* Collision confidence
* Relative speed
* Motion details

---

# Screenshots

```text id="r24"
outputs/screenshots/
```

Contains:

* Collision evidence frames

---

# Optimizations Implemented

## Improved Motion Analytics

* EMA speed smoothing
* Motion stability analysis
* Adaptive thresholds
* Motion consistency scoring

## Improved Collision Detection

* Dense traffic suppression
* Parallel-flow rejection
* Adaptive distance reasoning
* Slow-speed collision support
* Multi-frame persistence

## Improved Tracking

* Stable trajectory handling
* Tracker age filtering
* Noise suppression

---

# Advantages of YOLO11 Approach

## High Detection Accuracy

YOLO11 Large provides:

* Precise bounding boxes
* Better localization
* Better small-object detection

## Better Practical Collision Detection

Compared to generic traffic analytics:

* Fewer false positives
* Better close-up collision handling
* Better dense traffic reasoning

## Production-Friendly

* Easier customization
* Easier debugging
* Better reasoning flexibility
* More practical real-world tuning

---

# Final Outcome

The project successfully demonstrates:

* Real-time vehicle detection
* Multi-object tracking
* Motion intelligence
* Intelligent collision reasoning
* GPU-accelerated analytics
* Practical traffic surveillance capabilities

The system is highly customizable and suitable for further production-level enhancements in smart traffic monitoring and road safety analytics.
