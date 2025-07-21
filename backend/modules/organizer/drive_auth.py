from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SERVICE_ACCOUNT_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def drive_auth():
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = Credentials.from_authorized_user_file(SERVICE_ACCOUNT_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("modules/organizer/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(SERVICE_ACCOUNT_FILE, "w") as token:
            token.write(creds.to_json())

    drive_service = build('drive', 'v3', credentials=creds)

    return drive_service