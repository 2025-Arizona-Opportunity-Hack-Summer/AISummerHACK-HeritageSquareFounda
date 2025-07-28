# drive_files.py
# This module provides functionality to list files in Google Drive using the authenticated service.
from modules.organizer.drive_auth import drive_auth

def list_drive_files():
    """
    List all files in Google Drive.
    Returns a list of file metadata dictionaries.
    """
    drive_service = drive_auth()
    results = drive_service.files().list(
        q="trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    results.get('files', [])

    # calculate total number of files
    total_files = len(results.get('files', []))
    print(f"Total files in Drive: {total_files}")

    #return files
    return results.get('files', [])