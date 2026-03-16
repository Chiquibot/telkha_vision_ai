from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import subprocess

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Telkha Vision AI Server Running",
        "docs": "/docs",
        "upload": "/upload"
    }

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
SORTED_DIR = BASE_DIR / "sorted"

INPUT_DIR.mkdir(exist_ok=True)
SORTED_DIR.mkdir(exist_ok=True)


# Upload endpoint
@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    filename = file.filename

    # Accept ZIP or RAR
    if not filename.lower().endswith((".zip", ".rar")):
        return {"error": "Only .zip or .rar files are allowed"}

    site_name = filename.split(".")[0]

    file_path = INPUT_DIR / filename

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[INFO] Processing site: {site_name}")

    # Run sorting script
    subprocess.run([
        "python",
        "backend/predict_and_sort.py",
        site_name
    ])

    return {
        "status": "processing complete",
        "site": site_name,
        "download": f"/download/{site_name}"
    }


# Download endpoint
@app.get("/download/{site}")
def download(site: str):

    zip_path = SORTED_DIR / f"{site}.zip"

    if not zip_path.exists():
        return {"error": "Sorted file not found"}

    return FileResponse(
        path=zip_path,
        filename=f"{site}.zip",
        media_type="application/zip"
    )