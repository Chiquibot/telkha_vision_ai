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
5. Sort images into equipment folders
6. Preserve unsorted images
7. Generate AI report
8. Optional boxed detection images
9. Cleanup temporary files
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import zipfile
import shutil
import subprocess
import json
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

# Optional debugging mode (bounding boxes)
SAVE_BOXED_IMAGES = False

SUPPORTED_IMAGES = [
    ".jpg",".jpeg",".png",".bmp",".tif",".tiff",".webp"
]

# ============================================================
# LOAD CLASSES
# ============================================================

def load_classes():

    if not CLASSES_PATH.exists():
        raise FileNotFoundError(f"Missing classes file {CLASSES_PATH}")

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

        print("[INFO] Extracting ZIP")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

    elif rar_path.exists():

        print("[INFO] Extracting RAR")

        subprocess.run([
            "unrar","x","-o+",
            str(rar_path),
            str(extract_path)
        ], check=True)

    else:
        raise FileNotFoundError("No archive found")

    flatten_images(extract_path)

# ============================================================
# FLATTEN IMAGE FOLDERS
# ============================================================

def flatten_images(folder):

    moved = 0

    for file in folder.rglob("*"):

        if file.suffix.lower() in SUPPORTED_IMAGES:

            dest = folder / file.name

            if file != dest:
                shutil.move(str(file), dest)
                moved += 1

    for sub in folder.glob("*"):
        if sub.is_dir():
            shutil.rmtree(sub)

    print(f"[INFO] Flattened {moved} images")

# ============================================================
# RUN YOLO DETECTION
# ============================================================

def run_detection(site_name):

    source = UPLOAD_DIR / site_name

    detect_cmd = [
        "python",
        str(YOLO_DETECT),
        "--weights", str(MODEL_PATH),
        "--source", str(source),
        "--project", str(SORTED_DIR),
        "--name", site_name,
        "--exist-ok",
        "--save-txt",
        "--conf", str(CONF_THRESHOLD)
    ]

    if SAVE_BOXED_IMAGES:
        detect_cmd.append("--save-img")

    print("[INFO] Running YOLO detection")

    subprocess.run(detect_cmd, check=True)

# ============================================================
# SORT IMAGES
# ============================================================

def sort_images(site_name):

    upload_path = UPLOAD_DIR / site_name
    labels_path = SORTED_DIR / site_name / "labels"

    classified = set()
    class_counts = {}

    total_images = 0
    unsorted = 0

    for label_file in labels_path.glob("*.txt"):

        base = label_file.stem
        image_path = None

        for ext in SUPPORTED_IMAGES:
            candidate = upload_path / (base + ext)
            if candidate.exists():
                image_path = candidate
                base = candidate.name
                break

        if not image_path:
            continue

        classes_found = set()

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

            classes_found.add(category)

        for category in classes_found:

            dest = SORTED_DIR / site_name / category
            dest.mkdir(parents=True, exist_ok=True)

            shutil.copy(image_path, dest / base)

            class_counts[category] = class_counts.get(category,0)+1

        if classes_found:
            classified.add(base)

    for img in upload_path.iterdir():

        if img.suffix.lower() not in SUPPORTED_IMAGES:
            continue

        total_images += 1

        if img.name not in classified:

            shutil.copy(img, SORTED_DIR / site_name / img.name)

            unsorted += 1

    return total_images, unsorted, class_counts

# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report(site_name, total, unsorted, class_counts):

    report = {
        "total_images": total,
        "unsorted_images": unsorted,
        "sorted_images": total-unsorted,
        "class_counts": class_counts
    }

    report_path = SORTED_DIR / site_name / "report.json"

    with open(report_path,"w") as f:
        json.dump(report,f,indent=4)

    print("[INFO] Report generated")

# ============================================================
# CLEANUP
# ============================================================

def cleanup(site_name):

    upload = UPLOAD_DIR / site_name

    if upload.exists():
        shutil.rmtree(upload)

# ============================================================
# MAIN PROCESS
# ============================================================

def process_site(site_name):

    print("------------------------------------------------")
    print(f"[INFO] Processing site: {site_name}")
    print("------------------------------------------------")

    extract_archive(site_name)

    run_detection(site_name)

    total, unsorted, class_counts = sort_images(site_name)

    generate_report(site_name,total,unsorted,class_counts)

    cleanup(site_name)

    print("[INFO] Processing completed")

# ============================================================
# CLI ENTRY
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Usage: python predict_and_sort.py SITENAME")
        exit(1)

    process_site(sys.argv[1])