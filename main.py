from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from processor import process_video
import shutil
import uuid
from pathlib import Path
import os
from typing import Optional

app = FastAPI(title="Badminton Posture & Shot Analyzer v1.2")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path("static/index.html")
    if not html_path.exists():
        return HTMLResponse("<h3>Upload endpoint available at /upload</h3>")
    html = html_path.read_text()
    return HTMLResponse(html)


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    enable_court_detection: bool = Form(True),
    enable_shuttle_tracking: bool = Form(True),
    enable_advanced_analysis: bool = Form(True)
):
    """
    Upload and process badminton video with configurable features.
    
    Parameters:
    - file: Video file to process
    - enable_court_detection: Enable court boundary detection (v1.1)
    - enable_shuttle_tracking: Enable shuttlecock tracking (v1.1)
    - enable_advanced_analysis: Enable perspective transform and professional comparison (v1.2)
    """
    # save uploaded file
    uid = uuid.uuid4().hex
    in_path = UPLOAD_DIR / f"{uid}_{file.filename}"
    out_video_path = OUTPUT_DIR / f"{uid}_annotated.mp4"
    report_path = OUTPUT_DIR / f"{uid}_report.json"

    with in_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # optionally pass model path from env
    shot_model_path = os.environ.get("SHOT_MODEL_PATH", None)

    # process with feature flags
    report = process_video(
        str(in_path), 
        str(out_video_path), 
        shot_model_path=shot_model_path,
        enable_court_detection=enable_court_detection,
        enable_shuttle_tracking=enable_shuttle_tracking,
        enable_advanced_analysis=enable_advanced_analysis
    )

    # save report
    import json
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return JSONResponse({
        "status": "done",
        "annotated_video": str(out_video_path),
        "report": report
    })


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="video/mp4")
