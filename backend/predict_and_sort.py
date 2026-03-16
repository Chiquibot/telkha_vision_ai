#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TELKHA VISION AI
Photo Sorting Engine

Workflow

1. Receive site archive (.zip or .rar)
2. Extract photos
3. Flatten folder structure
4. Run YOLO detection
5. Sort images based on detected telecom equipment
6. Preserve unsorted images
7. Remove temporary files

Supports MULTI-CLASS sorting.
One image can appear in multiple equipment folders.
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


import zipfile
import shutil
import subprocess
import os
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

CONF_THRESHOLD = 0.35

SUPPORTED_IMAGES = [
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tif", ".tiff", ".webp"
]

# ============================================================
# LOAD CLASS NAMES
# ============================================================

def load_classes():

    if not CLASSES_PATH.exists():
        raise FileNotFoundError(f"Classes file missing: {CLASSES_PATH}")

    with open(CLASSES_PATH) as f:
        classes = [c.strip() for c in f.readlines() if c.strip()]

    print(f"[INFO] Loaded {len(classes)} classes")

    return classes


CATEGORY_NAMES = load_classes()

# ============================================================
# EXTRACT ARCHIVE
# ============================================================

def extract_archive(site_name):

    zip_path = INPUT_DIR / f"{site_name}.zip"
    rar_path = INPUT_DIR / f"{site_name}.rar"

    extract_path = UPLOAD_DIR / site_name
    extract_path.mkdir(parents=True, exist_ok=True)

    if zip_path.exists():

        print("[INFO] Extracting ZIP archive")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

    elif rar_path.exists():

        print("[INFO] Extracting RAR archive")

        subprocess.run([
            "unrar", "x", "-o+",
            str(rar_path),
            str(extract_path)
        ], check=True)

    else:

        raise FileNotFoundError(
            f"No archive found for site {site_name}"
        )

    print(f"[INFO] Archive extracted → {extract_path}")

    flatten_images(extract_path)

# ============================================================
# FLATTEN NESTED FOLDERS
# ============================================================

def flatten_images(site_folder):

    moved = 0

    for file in site_folder.rglob("*"):

        if file.suffix.lower() in SUPPORTED_IMAGES:

            dest = site_folder / file.name

            if file != dest:
                shutil.move(str(file), dest)
                moved += 1

    for folder in site_folder.glob("*"):
        if folder.is_dir():
            shutil.rmtree(folder)

    print(f"[INFO] Flattened folders ({moved} images moved)")

# ============================================================
# RUN YOLO DETECTION
# ============================================================

def run_detection(site_name):

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    source_path = UPLOAD_DIR / site_name

    print("[INFO] Running YOLO detection")

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
# SORT IMAGES
# ============================================================

def sort_images(site_name):

    upload_path = UPLOAD_DIR / site_name
    labels_path = SORTED_DIR / site_name / "labels"

    if not labels_path.exists():
        print("[WARNING] No YOLO labels found")
        return

    classified_images = set()

    for label_file in labels_path.glob("*.txt"):

        image_name = label_file.stem
        image_path = None

        for ext in SUPPORTED_IMAGES:
            candidate = upload_path / (image_name + ext)
            if candidate.exists():
                image_path = candidate
                image_name = candidate.name
                break

        if not image_path:
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

        for category in detected_classes:

            dest_folder = SORTED_DIR / site_name / category
            dest_folder.mkdir(parents=True, exist_ok=True)

            shutil.copy(image_path, dest_folder / image_name)

        if detected_classes:
            classified_images.add(image_name)

    root_output = SORTED_DIR / site_name

    for img in upload_path.iterdir():

        if img.suffix.lower() not in SUPPORTED_IMAGES:
            continue

        if img.name not in classified_images:
            shutil.copy(img, root_output / img.name)

    print("[INFO] Image sorting complete")

# ============================================================
# CLEANUP
# ============================================================

def cleanup(site_name):

    upload_path = UPLOAD_DIR / site_name

    if upload_path.exists():
        shutil.rmtree(upload_path)

    print("[INFO] Temporary files removed")

# ============================================================
# MAIN PROCESS
# ============================================================

def process_site(site_name):

    print("------------------------------------------------")
    print(f"[INFO] Processing site: {site_name}")
    print("------------------------------------------------")

    extract_archive(site_name)

    run_detection(site_name)

    sort_images(site_name)

    cleanup(site_name)

    print("[INFO] Site processing completed")

# ============================================================
# CLI ENTRY
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Usage:")
        print("python predict_and_sort.py SITENAME")
        exit(1)

    site_name = sys.argv[1]

    process_site(site_name)