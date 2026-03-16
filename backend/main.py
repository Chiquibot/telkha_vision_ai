from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import subprocess
import json
import sys
import threading
import time

app = FastAPI()

# --------------------------------------------------
# HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Telkha Vision AI Server Running",
        "docs": "/docs",
        "upload_endpoint": "/upload",
        "download_endpoint": "/download/{site}"
    }


# --------------------------------------------------
# CORS (Allow React frontend)
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# PROJECT DIRECTORIES
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "input"
UPLOAD_DIR = BASE_DIR / "uploads"
SORTED_DIR = BASE_DIR / "sorted"
DEBUG_DIR = BASE_DIR / "debug"

INPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
SORTED_DIR.mkdir(exist_ok=True)
DEBUG_DIR.mkdir(exist_ok=True)

# Serve debug images so the frontend can preview bounding boxes
app.mount("/debug_images", StaticFiles(directory=DEBUG_DIR), name="debug_images")


# --------------------------------------------------
# UPLOAD ENDPOINT
# --------------------------------------------------

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    filename = file.filename

    if not filename.lower().endswith((".zip", ".rar")):
        return {"error": "Only .zip or .rar files are allowed"}

    site_name = Path(filename).stem

    input_path = INPUT_DIR / filename
    upload_path = UPLOAD_DIR / site_name
    sorted_path = SORTED_DIR / site_name
    debug_path = DEBUG_DIR / site_name
    zip_path = SORTED_DIR / f"{site_name}_sorted.zip"

    # --------------------------------------------------
    # CLEAN PREVIOUS RUN
    # --------------------------------------------------

    if upload_path.exists():
        shutil.rmtree(upload_path)

    if sorted_path.exists():
        shutil.rmtree(sorted_path)

    if debug_path.exists():
        shutil.rmtree(debug_path)

    if zip_path.exists():
        zip_path.unlink()

    # --------------------------------------------------
    # SAVE UPLOADED FILE
    # --------------------------------------------------

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[INFO] Uploaded site: {site_name}")

    # --------------------------------------------------
    # RUN AI SORTING ENGINE
    # --------------------------------------------------

    try:

        process = subprocess.run(
            [sys.executable, "backend/predict_and_sort.py", site_name],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            return {
                "status": "error",
                "message": "AI sorting failed",
                "details": process.stderr
            }

    except Exception as e:

        return {
            "status": "error",
            "message": "Failed to execute sorting engine",
            "details": str(e)
        }

    print("[INFO] Sorting completed")


    # --------------------------------------------------
    # AUTO DELETE DEBUG IMAGES AFTER 15 MINUTES
    # --------------------------------------------------

    def cleanup_debug():
        time.sleep(900)  # 15 minutes
        debug_folder = DEBUG_DIR / site_name
        if debug_folder.exists():
            try:
                shutil.rmtree(debug_folder)
                print(f"[INFO] Debug images for {site_name} removed")
            except Exception as e:
                print(f"[WARNING] Failed to cleanup debug images: {e}")

    threading.Thread(target=cleanup_debug, daemon=True).start()


    # --------------------------------------------------
    # LOAD AI REPORT
    # --------------------------------------------------

    report_path = SORTED_DIR / site_name / "report.json"

    if report_path.exists():

        with open(report_path) as f:
            report_data = json.load(f)

    else:

        report_data = {
            "total_images": 0,
            "sorted_images": 0,
            "unsorted_images": 0,
            "class_counts": {},
            "class_confidence": {}
        }

    # --------------------------------------------------
    # RETURN RESPONSE
    # --------------------------------------------------

    return {
        "status": "complete",
        "site": site_name,
        "download": f"/download/{site_name}",
        "debug_images": f"/debug/{site_name}",
        "report": report_data
    }


# --------------------------------------------------
# DOWNLOAD SORTED RESULTS
# --------------------------------------------------

@app.get("/download/{site}")
def download(site: str):

    site_folder = SORTED_DIR / site

    if not site_folder.exists():
        return {"error": "Sorted folder not found"}

    zip_path = SORTED_DIR / f"{site}_sorted.zip"

    # Create zip dynamically
    shutil.make_archive(
        str(zip_path).replace(".zip", ""),
        "zip",
        root_dir=site_folder
    )

    return FileResponse(
        path=zip_path,
        filename=f"{site}_sorted.zip",
        media_type="application/zip"
    )


# --------------------------------------------------
# OPTIONAL DEBUG IMAGE VIEWER
# --------------------------------------------------

@app.get("/debug/{site}")
def debug(site: str):

    debug_folder = DEBUG_DIR / site

    if not debug_folder.exists():
        return {"error": "Debug folder not found or expired"}

    images = []

    for img in debug_folder.glob("*"):
        if img.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            images.append(f"/debug_images/{site}/{img.name}")

    return {
        "site": site,
        "debug_images": images
    }