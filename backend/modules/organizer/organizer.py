# categorizer.py

import io
import pdfplumber
import docx
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google import genai
import re
import difflib
from dotenv import load_dotenv
import os
import pytesseract
from PIL import Image

# === CONFIGURATION ===
SERVICE_ACCOUNT_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not GENAI_API_KEY:
    raise ValueError("GENAI_API_KEY not found in environment variables. Please set it in your .env file.")

client = genai.Client(api_key=GENAI_API_KEY)

# === GOOGLE DRIVE AUTH ===
creds = None
if os.path.exists(SERVICE_ACCOUNT_FILE):
    creds = Credentials.from_authorized_user_file(SERVICE_ACCOUNT_FILE, SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open(SERVICE_ACCOUNT_FILE, "w") as token:
        token.write(creds.to_json())

drive_service = build('drive', 'v3', credentials=creds)

# === DYNAMIC FOLDER FETCHING & FUZZY MATCHING ===
def get_existing_folders():
    """Return a dict of {folder_name_lower: folder_id} for all folders in the Drive."""
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    return {folder['name'].strip().lower(): folder['id'] for folder in results.get('files', [])}

def find_best_folder_match(category, existing_folders, cutoff=0.8):
    """
    Find the best matching folder for the category using fuzzy matching.
    Returns the folder name (lowercase) if found, else None.
    """
    category_lower = category.strip().lower()
    folder_names = list(existing_folders.keys())
    matches = difflib.get_close_matches(category_lower, folder_names, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return None

def ensure_folder(category, existing_folders):
    """Ensure a folder exists for the category, create if needed, and return its ID."""
    category_lower = category.strip().lower()
    # Try fuzzy match first
    best_match = find_best_folder_match(category, existing_folders)
    if best_match:
        print(f"Using existing folder: {best_match} for category: {category}")
        return existing_folders[best_match]
    # If no match, create folder
    folder_metadata = {
        'name': category,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    folder_id = folder['id']
    existing_folders[category_lower] = folder_id
    print(f"Created folder: {category}")
    return folder_id

def move_file_to_folder(file_id, folder_id, category):
    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))
    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    print(f"Moved file to folder: {category}")

# === TEXT & IMAGE EXTRACTION ===
def extract_text_from_image(file_data):
    try:
        file_data.seek(0)
        image = Image.open(file_data)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""

def categorize_image_with_genai_vision(file_data):
    try:
        file_data.seek(0)
        try:
            img = Image.open(file_data)
            img.verify()
        except Exception as img_e:
            print(f"Image verification failed: {img_e}")
            return "Uncategorized"
        file_data.seek(0)
        prompt = (
            "Categorize the following image based on its content and suggest 1 relevant tag.\n"
            "Please provide a single category that best describes the image.\n"
        )
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    {"role": "user", "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": file_data.getvalue()}}
                    ]}
                ]
            )
            return extract_category_from_response(response)
        except genai.errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                print("Gemini API quota exceeded. Please wait or upgrade your plan.")
                return "Uncategorized"
            else:
                raise
    except Exception as e:
        print(f"Vision categorization failed: {e}")
        return "Uncategorized"

def download_file_content(file_id, mime_type):
    request = drive_service.files().get_media(fileId=file_id)
    file_data = io.BytesIO()
    print(f"Downloading file {file_id}...")
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_data.seek(0)
    try:
        if mime_type == "application/pdf":
            with pdfplumber.open(file_data) as pdf:
                return "\n".join(page.extract_text() or '' for page in pdf.pages)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file_data)
            return "\n".join(p.text for p in doc.paragraphs)
        elif mime_type.startswith("image/"):
            print("Image file detected, extracting text with OCR...")
            text = extract_text_from_image(file_data)
            return text, file_data
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from file {file_id}: {e}")
        return ""

def categorize_and_tag_geminiai(text):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"Categorize the following document and suggest 1 relevant tag.\nText:\n{text}\n\n"]
        )
        return response
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            print("Gemini API quota exceeded. Please wait or upgrade your plan.")
            # Optionally: exit() or return a default value
            return None
        else:
            raise

def extract_category_from_response(response):
    try:
        raw_text = None
        if hasattr(response, 'text'):
            raw_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                part = candidate.content.parts[0]
                if hasattr(part, 'text'):
                    raw_text = part.text
        if not raw_text:
            return "Uncategorized"
        match = re.search(r"\*\*Category:\*\*\s*\n?\s*[*-]?\s*(.+)", raw_text)
        if match:
            category_line = match.group(1).strip()
            category_line = re.sub(r"[*]", "", category_line)
            category = category_line.split('\n')[0].strip()
            print(f"Extracted category: {category}")
            return category if category else "Uncategorized"
    except Exception as e:
        print(f"Error extracting category: {e}")
    return "Uncategorized"

# === BATCH CATEGORIZATION & MOVING ===
def batch_categorize_files(files):
    existing_folders = get_existing_folders()
    category_to_files = {}
    for file in files:
        file_id, file_name, mime_type = file['id'], file['name'], file['mimeType']
        print(f"\nProcessing: {file_name}")
        if mime_type.startswith("image/"):
            content, file_data = download_file_content(file_id, mime_type)
            if not content or not content.strip():
                category = categorize_image_with_genai_vision(file_data)
            else:
                response = categorize_and_tag_geminiai(content)
                category = extract_category_from_response(response)
        else:
            content = download_file_content(file_id, mime_type)
            if not content.strip():
                category = "Uncategorized"
            else:
                response = categorize_and_tag_geminiai(content)
                category = extract_category_from_response(response)
        category = category.strip()
        print(f"Classified as: {category}")
        category_to_files.setdefault(category, []).append(file_id)
    return category_to_files, existing_folders

def batch_move_files(category_to_files, existing_folders):
    for category, file_ids in category_to_files.items():
        folder_id = ensure_folder(category, existing_folders)
        for file_id in file_ids:
            move_file_to_folder(file_id, folder_id, category)

def process_all_drive_files():
    image_mimes = [
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff"
    ]
    mime_query = " or ".join([f"mimeType='{m}'" for m in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ] + image_mimes])
    query = f"({mime_query}) and trashed=false"
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()
    files = results.get('files', [])
    print(f"Found {len(files)} files to process.")
    category_to_files, existing_folders = batch_categorize_files(files)
    batch_move_files(category_to_files, existing_folders)


def remove_empty_folders():
    """Delete all empty folders in the Drive (not trashed)."""
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    print(f"Checking {len(folders)} folders for emptiness...")

    for folder in folders:
        # Check if the folder contains any files (including subfolders)
        children = drive_service.files().list(
            q=f"'{folder['id']}' in parents and trashed=false",
            fields="files(id)"
        ).execute()
        if not children.get('files'):
            print(f"Deleting empty folder: {folder['name']}")
            drive_service.files().delete(fileId=folder['id']).execute()


def group_similar_folders(existing_folders, cutoff=0.8):
    """
    Groups similar folder names using fuzzy matching.
    Returns a dict: {canonical_folder_name: [duplicate_folder_names]}
    """
    folder_names = list(existing_folders.keys())
    grouped = {}
    used = set()
    for name in folder_names:
        if name in used:
            continue
        matches = difflib.get_close_matches(name, folder_names, n=len(folder_names), cutoff=cutoff)
        # Pick the shortest name as canonical (or you can use another rule)
        canonical = min(matches, key=len)
        grouped.setdefault(canonical, [])
        for m in matches:
            if m != canonical:
                grouped[canonical].append(m)
                used.add(m)
        used.add(canonical)
    return grouped

def merge_and_cleanup_folders(existing_folders, cutoff=0.8):
    """
    Moves files from similar folders into a canonical folder and deletes duplicates.
    """
    grouped = group_similar_folders(existing_folders, cutoff)
    for canonical, duplicates in grouped.items():
        canonical_id = existing_folders[canonical]
        for dup_name in duplicates:
            dup_id = existing_folders[dup_name]
            # Move all files from dup_id to canonical_id
            children = drive_service.files().list(
                q=f"'{dup_id}' in parents and trashed=false",
                fields="files(id, name)"
            ).execute().get('files', [])
            for child in children:
                drive_service.files().update(
                    fileId=child['id'],
                    addParents=canonical_id,
                    removeParents=dup_id,
                    fields='id, parents'
                ).execute()
                print(f"Moved '{child['name']}' from '{dup_name}' to '{canonical}'")
            # Delete the now-empty duplicate folder
            drive_service.files().delete(fileId=dup_id).execute()
            print(f"Deleted duplicate folder: {dup_name}")
            # Remove the deleted folder from the dictionary to avoid future errors
            del existing_folders[dup_name]

# Example usage after categorization and moving:
if __name__ == "__main__":
    print("Starting Drive categorization...")
    process_all_drive_files()
    existing_folders = get_existing_folders()
    merge_and_cleanup_folders(existing_folders, cutoff=0.4)
    remove_empty_folders()
    print("Done.")
