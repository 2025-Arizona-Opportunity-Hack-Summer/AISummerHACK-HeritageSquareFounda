from modules.organizer.drive_auth import drive_auth
from googleapiclient.http import MediaFileUpload
import os

def upload_file(file_path, folder_id=None):
    """
    Upload a file to Google Drive.
    :param file_path: Path to the file to upload.
    :param folder_id: ID of the folder to upload the file into (optional).
    :return: The uploaded file's metadata.
    """
    drive_service = drive_auth()

    # Define metadata for the file and folder = root
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id] if folder_id else []
    }

    # Upload
    media = MediaFileUpload(
        file_path,
        resumable=True
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, mimeType, parents"
    ).execute()
    print(f"Uploaded file '{file.get('name')}' with ID: {file.get('id')}")
    return file

if __name__ == "__main__":
    # Example usage
    # Ask the user for a file path to upload
    file_path = input("Enter the path of the file to upload: ")
    if not os.path.exists(file_path):
        print("File does not exist. Please check the path and try again.")
    else:
        upload_file(file_path)