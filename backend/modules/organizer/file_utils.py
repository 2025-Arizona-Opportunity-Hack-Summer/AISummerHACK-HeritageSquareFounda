from googleapiclient.http import MediaIoBaseDownload
from modules.organizer.drive_auth import drive_auth
import io
import pdfplumber
import docx
from PIL import Image
import pytesseract

drive_service = drive_auth()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

def extract_text_from_image(file_data):
    try:
        file_data.seek(0)
        image = Image.open(file_data)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""