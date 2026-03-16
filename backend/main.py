from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import subprocess

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

    site_name = filename.split(".")[0]

    input_path = INPUT_DIR / filename
    upload_site_path = UPLOAD_DIR / site_name
    sorted_site_path = SORTED_DIR / site_name

    # --------------------------------------------------
    # CLEAN PREVIOUS RUN (important)
    # --------------------------------------------------

    if upload_site_path.exists():
        shutil.rmtree(upload_site_path)

    if sorted_site_path.exists():
        shutil.rmtree(sorted_site_path)

    # --------------------------------------------------
    # SAVE UPLOADED FILE
    # --------------------------------------------------

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[INFO] Processing site: {site_name}")

    # --------------------------------------------------
    # RUN SORTING SCRIPT
    # --------------------------------------------------

    try:
        subprocess.run(
            ["python", "backend/predict_and_sort.py", site_name],
            check=True
        )
    except subprocess.CalledProcessError:
        return {"error": "AI processing failed"}

    return {
        "status": "processing complete",
        "site": site_name,
        "download": f"/download/{site_name}"
    }

# --------------------------------------------------
# DOWNLOAD ENDPOINT
# --------------------------------------------------

@app.get("/download/{site}")
def download(site: str):

    site_folder = SORTED_DIR / site

    if not site_folder.exists():
        return {"error": "Sorted folder not found"}

    zip_path = SORTED_DIR / f"{site}_sorted"

    # --------------------------------------------------
    # CREATE ZIP FROM SORTED FOLDER
    # --------------------------------------------------

    shutil.make_archive(
        str(zip_path),
        'zip',
        site_folder
    )

    return FileResponse(
        path=f"{zip_path}.zip",
        filename=f"{site}_sorted.zip",
        media_type="application/zip"
    )