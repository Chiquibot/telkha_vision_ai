from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import subprocess
import json

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
# CORS (React frontend access)
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

INPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
SORTED_DIR.mkdir(exist_ok=True)

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

    # ---------------------------------------------
    # CLEAN PREVIOUS RUN
    # ---------------------------------------------

    if upload_path.exists():
        shutil.rmtree(upload_path)

    if sorted_path.exists():
        shutil.rmtree(sorted_path)

    # ---------------------------------------------
    # SAVE UPLOADED FILE
    # ---------------------------------------------

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[INFO] Processing site: {site_name}")

    # ---------------------------------------------
    # RUN SORTING ENGINE
    # ---------------------------------------------

    try:

        subprocess.run(
            ["python", "backend/predict_and_sort.py", site_name],
            check=True
        )

    except subprocess.CalledProcessError as e:

        return {
            "status": "error",
            "message": "AI sorting failed",
            "details": str(e)
        }

    # ---------------------------------------------
    # LOAD REPORT
    # ---------------------------------------------

    report_path = SORTED_DIR / site_name / "report.json"

    report_data = {}

    if report_path.exists():

        with open(report_path) as f:
            report_data = json.load(f)

    else:

        report_data = {
            "total_images": 0,
            "sorted_images": 0,
            "unsorted_images": 0,
            "class_counts": {}
        }

    # ---------------------------------------------
    # RETURN RESPONSE TO FRONTEND
    # ---------------------------------------------

    return {
        "status": "complete",
        "site": site_name,
        "download": f"/download/{site_name}",
        "report": report_data
    }

# --------------------------------------------------
# DOWNLOAD SORTED RESULT
# --------------------------------------------------

@app.get("/download/{site}")
def download(site: str):

    site_folder = SORTED_DIR / site

    if not site_folder.exists():
        return {"error": "Sorted folder not found"}

    zip_path = SORTED_DIR / f"{site}_sorted.zip"

    # Create zip if not existing
    if not zip_path.exists():

        shutil.make_archive(
            str(zip_path).replace(".zip", ""),
            "zip",
            site_folder
        )

    return FileResponse(
        path=zip_path,
        filename=f"{site}_sorted.zip",
        media_type="application/zip"
    )