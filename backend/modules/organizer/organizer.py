# categorizer.py

import io
import pdfplumber
import docx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from openai import OpenAI

# === CONFIGURATION ===
SERVICE_ACCOUNT_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
PROJECT_ID = "categorizer-464114"  # Only required for Vertex AI (not used here)
client = OpenAI(api_key=("OPENAI_API_KEY"))

# === MANUAL CATEGORIES ===
# CATEGORIES = {
#     "Development": ["donor", "fundraising", "grant", "event", "sponsorship"],
#     "Marketing": ["poster", "campaign", "ad", "social media", "brand", "pricing"],
#     "Operations": ["workflow", "logistics", "inventory"],
#     "Research": ["historic", "archive", "data", "source", "record"],
#     "Board of Directors": ["board", "meeting", "minutes", "trustees"],
#     "Programming": ["schedule", "activities", "calendar"],
#     "Employee Resources": ["contract", "policy", "leave", "benefits", "training"],
#     "Accounting": ["invoice", "budget", "expenses", "finance", "balance"],
#     "Curation": ["exhibit", "collection", "display", "artifacts"],
#     "Images": ["photo", "image", "jpg", "png", "jpeg"]
# }


# === INITIALIZE GOOGLE APIs ===
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

if os.path.exists("token.json"):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  else:
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    
  # Save the credentials for the next run
  with open("token.json", "w") as token:
    token.write(creds.to_json())

# Google Drive
drive_service = build('drive', 'v3', credentials=creds)


# === TEXT EXTRACTION ===
def download_file_content(file_id, mime_type):
    request = drive_service.files().get_media(fileId=file_id)
    file_data = io.BytesIO()
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

        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from file {file_id}: {e}")
        return ""


# === MANUAL KEYWORD CLASSIFICATION ===
# # def classify_document_by_keywords(text):
#     text = text.lower()
#     category_scores = {}

#     for category, keywords in CATEGORIES.items():
#         score = sum(text.count(keyword) for keyword in keywords)
#         category_scores[category] = score

#     best_category = max(category_scores, key=category_scores.get)
#     if category_scores[best_category] > 0:
#         return best_category
#     return "Uncategorized"

# ===== CATEGORIZE USING AI ===
def categorize_and_tag_openai(text):
    prompt = (
        "Categorize the following document and suggest 3-5 relevant tags."
        "Text:\n" + text + "\n\n"
        "Respond in this JSON format: {\"category\": \"<category>\", \"tags\": [\"tag1\", \"tag2\", ...]}"
    )
    response = client.chat.completions.create(
        model = "gpt-4",
        messages = [{"role":"user", "content": prompt}]
    )
    result = eval(response['choices'][0]['messages']['content'])
    return result['category'], result['tags']

# === MOVE FILE TO CATEGORY FOLDER ===
def move_file_to_category(file_id, category):
    results = drive_service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{category}' and trashed=false",
        fields="files(id, name)"
    ).execute()

    if results['files']:
        folder_id = results['files'][0]['id']
    else:
        folder_metadata = {
            'name': category,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder['id']

    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))

    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()


# === FILE CLASSIFICATION & ORGANIZATION ===
def categorize_and_move_file(file_id, file_name, mime_type):
    print(f"\nProcessing: {file_name}")
    content = download_file_content(file_id, mime_type)

    if not content.strip():
        print("No extractable content found.")
        category = "Uncategorized"
    else:
        #category = classify_document_by_keywords(content)
        category, tags = categorize_and_tag_openai(content)

    print(f"Classified as: {category}, with tags: {tags}")
    move_file_to_category(file_id, category)
    add_tags_to_file(drive_service, file_id, tags)
    print(f"Moved '{file_name}' to folder: {category}")

# === ADD TAGS TO GOOGLE DRIVE FILES ===
def add_tags_to_file(drive_service, file_id, tags):
    custom_properties = {f"tag_{i}": tag for i, tag in enumerate(tags)}
    file_metadata = {'properties': custom_properties}
    drive_service.files().update(
        fileId = file_id,
        body = file_metadata,
        fileIds = 'id, properties'
    ).execute()


# === BATCH PROCESS FILES ===
def process_all_drive_files():
    results = drive_service.files().list(
        q="mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
        fields="files(id, name, mimeType)"
    ).execute()

    for file in results.get('files', []):
        categorize_and_move_file(file['id'], file['name'], file['mimeType'])

# === MAIN ===
if __name__ == "__main__":
    print("Starting AI-free, keyword-based categorization of Drive files...")
    process_all_drive_files()
    print("Done.")
