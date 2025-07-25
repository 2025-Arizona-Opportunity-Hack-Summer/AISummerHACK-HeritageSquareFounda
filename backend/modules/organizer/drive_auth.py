# drive_auth.py
# This module handles Google Drive authentication using either a service account for production or OAuth 2.
import json
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
ENV = os.getenv("ENV", "development")  # Set to "production" in prod
SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")  # JSON key content for production
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "service-account-key.json")
CREDENTIALS_FILE = "modules/organizer/credentials.json"
TOKEN_FILE = "token.json"

def drive_auth():
    creds = None
    try:
        if ENV == "production":
            # Use service account key from environment variable for production
            if not SERVICE_ACCOUNT_KEY:
                raise Exception("GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")
            service_account_info = json.loads(SERVICE_ACCOUNT_KEY)
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
        else:
            # Use OAuth 2.0 for development
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(CREDENTIALS_FILE):
                        raise Exception(f"Credentials file not found at {CREDENTIALS_FILE}")
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())

        # Build and return the Drive service
        drive_service = build('drive', 'v3', credentials=creds)
        return drive_service

    except json.JSONDecodeError:
        raise Exception("Invalid GOOGLE_SERVICE_ACCOUNT_KEY format")
    except FileNotFoundError as e:
        raise Exception(f"File not found: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Drive API: {str(e)}")