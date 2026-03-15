#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 09:01:57 2026

@author: macbookairm1256
"""

"""
TELKHA VISION AI
Photo Sorting Engine

This script performs the following workflow:

1. Accept a site ZIP file from the input folder
2. Extract the photos
3. Run YOLO object detection
4. Sort images into folders based on detected classes
5. Preserve unsorted images in the root folder

This version supports MULTI-CLASS sorting.
One image may appear in multiple equipment folders.

Example result:

sorted/
   SITE001/
      antenna/
      rectifier/
      microwave/
      photo123.jpg   ← unsorted image
"""

import zipfile
import shutil
import subprocess
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path.home() / "telkha_vision_ai"

INPUT_DIR = BASE_DIR / "input"
UPLOAD_DIR = BASE_DIR / "uploads"
SORTED_DIR = BASE_DIR / "sorted"
MODEL_DIR = BASE_DIR / "models"
CONFIG_DIR = BASE_DIR / "config"

MODEL_PATH = MODEL_DIR / "best.pt"
CLASSES_PATH = CONFIG_DIR / "classes.txt"

YOLO_DETECT = BASE_DIR / "yolov5" / "detect.py"

# Minimum confidence threshold
CONF_THRESHOLD = 0.60


# ============================================================
# LOAD CLASS NAMES
# ============================================================

def load_classes():
    """
    Loads class names from classes.txt

    Example:
    antenna
    rectifier
    microwave
    """

    if not CLASSES_PATH.exists():
        raise FileNotFoundError(f"Classes file not found: {CLASSES_PATH}")

    with open(CLASSES_PATH) as f:
        classes = [c.strip() for c in f.readlines() if c.strip()]

    return classes


CATEGORY_NAMES = load_classes()


# ============================================================
# UNZIP SITE PHOTOS
# ============================================================

def unzip_site(site_name):
    """
    Extracts site photos from ZIP file.

    Input:
        input/SITE001.zip

    Output:
        uploads/SITE001/*.jpg
    """

    zip_path = INPUT_DIR / f"{site_name}.zip"

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    extract_path = UPLOAD_DIR / site_name
    extract_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    print(f"[INFO] ZIP extracted → {extract_path}")


# ============================================================
# RUN YOLO DETECTION
# ============================================================

def run_detection(site_name):
    """
    Runs YOLOv5 object detection on uploaded images.

    YOLO will generate label files:

    sorted/SITE001/labels/*.txt
    """

    source_path = UPLOAD_DIR / site_name

    print("[INFO] Running YOLO detection...")

    detect_cmd = [
        "python",
        str(YOLO_DETECT),
        "--weights", str(MODEL_PATH),
        "--source", str(source_path),
        "--project", str(SORTED_DIR),
        "--name", site_name,
        "--exist-ok",
        "--save-txt",
        "--conf", str(CONF_THRESHOLD)
    ]

    subprocess.run(detect_cmd, check=True)


# ============================================================
# SORT IMAGES INTO CLASS FOLDERS
# ============================================================

def sort_images(site_name):
    """
    Reads YOLO label files and sorts images into folders.

    Supports MULTI-CLASS detection.

    Example:
        photo123.jpg
            antenna
            rectifier

    Result:
        antenna/photo123.jpg
        rectifier/photo123.jpg
    """

    upload_path = UPLOAD_DIR / site_name
    labels_path = SORTED_DIR / site_name / "labels"

    if not labels_path.exists():
        print("[WARNING] No labels found. Nothing to sort.")
        return

    classified_images = set()

    for label_file in labels_path.glob("*.txt"):

        image_name = label_file.stem + ".jpg"
        image_path = upload_path / image_name

        if not image_path.exists():
            continue

        detected_classes = set()

        with open(label_file) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        for line in lines:

            parts = line.split()

            if len(parts) < 5:
                continue

            class_id = int(parts[0])

            if class_id >= len(CATEGORY_NAMES):
                continue

            category = CATEGORY_NAMES[class_id]
            detected_classes.add(category)

        # Copy image into each detected class folder
        for category in detected_classes:

            dest_folder = SORTED_DIR / site_name / category
            dest_folder.mkdir(parents=True, exist_ok=True)

            shutil.copy(image_path, dest_folder / image_name)

        if detected_classes:
            classified_images.add(image_name)

    # Preserve unsorted images
    root_output = SORTED_DIR / site_name

    for img in upload_path.glob("*.jpg"):

        if img.name not in classified_images:
            shutil.copy(img, root_output / img.name)

    print("[INFO] Image sorting complete")


# ============================================================
# CLEAN TEMPORARY FILES
# ============================================================

def cleanup(site_name):
    """
    Removes temporary upload folder to save disk space.
    """

    upload_path = UPLOAD_DIR / site_name

    if upload_path.exists():
        shutil.rmtree(upload_path)

    print("[INFO] Temporary upload folder removed")


# ============================================================
# MAIN PROCESS
# ============================================================

def process_site(site_name):

    print(f"[INFO] Processing site: {site_name}")

    unzip_site(site_name)

    run_detection(site_name)

    sort_images(site_name)

    cleanup(site_name)

    print("[INFO] Processing completed successfully")


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Usage: python predict_and_sort.py SITENAME")
        exit(1)

    site_name = sys.argv[1]

    process_site(site_name)