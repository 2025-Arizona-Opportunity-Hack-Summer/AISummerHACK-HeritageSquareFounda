#routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from modules.organizer.categorizer import process_all_drive_files
from modules.organizer.upload_file import upload_file
from modules.organizer.folder_utils import merge_and_cleanup_folders, get_existing_folders, remove_empty_folders
from modules.organizer.drive_files import list_drive_files
import logging
import os
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
class APIResponse(BaseModel):
    status: str
    message: str

@router.get("/", response_model=APIResponse)
async def root():
    return APIResponse(status="ok", message="API is running")

@router.get("/files", response_model=list)
async def list_files():
    try:
        files = list_drive_files()
        # Log total files found
        logger.info(f"Total files found: {len(files)}")
        # return APIResponse with number of files
        return APIResponse(status="success", message=f"Found {len(files)} files")
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

@router.post("/categorize", response_model=APIResponse)
async def run_categorizer():
    try:
        logger.info("Starting Drive categorization...")
        process_all_drive_files()
        logger.info("Drive categorization complete.")
        return APIResponse(status="success", message="Files categorized successfully")
    except Exception as e:
        logger.error(f"Categorization error: {str(e)}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

@router.post("/upload", response_model=APIResponse)
async def run_upload(file: UploadFile = File(...)):
    try:
        # Define a safe upload directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(upload_dir, safe_filename)

        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Verify file exists
        if not os.path.exists(file_path):
            logger.error("Uploaded file could not be saved.")
            raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

        # Call upload_file
        upload_file(file_path)
        logger.info(f"File {safe_filename} uploaded successfully")

        # Clean up (optional, keep if needed for later use)
        os.remove(file_path)
        return APIResponse(status="success", message=f"File {safe_filename} uploaded successfully")
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

@router.post("/cleanup", response_model=APIResponse)
async def run_cleanup():
    try:
        remove_empty_folders()
        logger.info("Cleanup complete.")
        return APIResponse(status="success", message="Empty folders removed successfully")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

@router.post("/merge", response_model=APIResponse)
async def run_merge():
    try:
        existing_folders = get_existing_folders()
        merge_and_cleanup_folders(existing_folders, cutoff=0.4)
        logger.info("Merge duplicate folders complete.")
        return APIResponse(status="success", message="Folders merged successfully")
    except Exception as e:
        logger.error(f"Merge error: {str(e)}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})
    