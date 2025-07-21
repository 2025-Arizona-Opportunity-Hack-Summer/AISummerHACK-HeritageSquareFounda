#routes.py
from fastapi import APIRouter
from modules.organizer.categorizer import process_all_drive_files
from modules.organizer.upload_file import upload_file

router = APIRouter()

@router.get("/")
def root():
    return {"status": "ok", "message": "API is running"}

@router.post("/categorize")
def run_categorizer():
    try:
        process_all_drive_files()
        return {"status": "success", "message": "Files categorized successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.put("/upload")
def run_upload():
    try:
        upload_file()
        return {"status": "success", "message": "File uploaded successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
