#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 09:04:01 2026

@author: macbookairm1256
"""

"""
TELKHA VISION AI
Dataset Analyzer

This tool analyzes the training dataset used for YOLO training.

It reports:
    - number of images per class
    - number of object instances per class
    - dataset imbalance
    - weak classes that need more data

This helps improve model accuracy by identifying
which equipment categories need more labeled photos.
"""

from pathlib import Path
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path.home() / "telkha_vision_ai"

DATASET_DIR = BASE_DIR / "datasets" / "training_data"
LABEL_DIR = DATASET_DIR / "labels" / "train"
IMAGE_DIR = DATASET_DIR / "images" / "train"

CLASSES_FILE = BASE_DIR / "config" / "classes.txt"

# Minimum recommended instances
MIN_INSTANCES = 200


# ============================================================
# LOAD CLASS NAMES
# ============================================================

def load_classes():

    if not CLASSES_FILE.exists():
        raise FileNotFoundError(f"Classes file missing: {CLASSES_FILE}")

    with open(CLASSES_FILE) as f:
        classes = [c.strip() for c in f.readlines() if c.strip()]

    return classes


# ============================================================
# DATASET ANALYSIS
# ============================================================

def analyze_dataset():

    classes = load_classes()

    instance_count = defaultdict(int)
    image_count = defaultdict(set)

    label_files = list(LABEL_DIR.glob("*.txt"))

    if not label_files:
        print("No label files found.")
        return

    for label_file in label_files:

        with open(label_file) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        for line in lines:

            parts = line.split()

            class_id = int(parts[0])

            if class_id >= len(classes):
                continue

            class_name = classes[class_id]

            instance_count[class_name] += 1
            image_count[class_name].add(label_file.name)

    print("\n===================================================")
    print("TELKHA VISION AI - DATASET REPORT")
    print("===================================================\n")

    for cls in classes:

        instances = instance_count[cls]
        images = len(image_count[cls])

        status = "OK"

        if instances < MIN_INSTANCES:
            status = "WEAK ⚠"

        print(f"{cls:25} images:{images:4} instances:{instances:5}  {status}")

    print("\n===================================================")

    total_images = len(list(IMAGE_DIR.glob("*.jpg")))
    total_labels = len(label_files)

    print(f"Total Images : {total_images}")
    print(f"Total Labels : {total_labels}")

    print("\nRecommended minimum per class:", MIN_INSTANCES)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    analyze_dataset()