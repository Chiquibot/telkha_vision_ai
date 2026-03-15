"""
Telkha Vision AI
Model Training Pipeline

This script trains a YOLO model using the dataset inside:

datasets/training_data

After training it automatically saves the best model to:

models/best.pt
"""

import os
import shutil
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_DIR = BASE_DIR / "datasets" / "training_data"
MODEL_DIR = BASE_DIR / "models"
YOLO_DIR = BASE_DIR / "yolov5"

DATA_YAML = DATASET_DIR / "dataset.yaml"


def train_model():

    print("Starting Telkha Vision AI training")

    train_command = [
        "python",
        str(YOLO_DIR / "train.py"),
        "--img", "640",
        "--batch", "16",
        "--epochs", "100",
        "--data", str(DATA_YAML),
        "--weights", "yolov5s.pt",
        "--project", str(BASE_DIR / "training_runs"),
        "--name", "telkha_training"
    ]

    subprocess.run(train_command)

    best_model = BASE_DIR / "training_runs" / "telkha_training" / "weights" / "best.pt"

    if best_model.exists():

        MODEL_DIR.mkdir(exist_ok=True)

        shutil.copy(best_model, MODEL_DIR / "best.pt")

        print("Model updated successfully")

    else:

        print("Training finished but best.pt not found")


if __name__ == "__main__":

    train_model()# -*- coding: utf-8 -*-

