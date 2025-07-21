#routes.py
from fastapi import APIRouter
from backend.modules.organizer.categorizer import process_all_drive_files

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