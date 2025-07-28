from modules.organizer.drive_auth import drive_auth
from modules.organizer.folder_utils import batch_move_files, merge_and_cleanup_folders, remove_empty_folders, get_existing_folders
from modules.organizer.categorization import batch_categorize_files

drive_service = drive_auth()

def process_all_drive_files():
    image_mimes = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff"]
    mime_query = " or ".join([f"mimeType='{m}'" for m in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ] + image_mimes])
    query = f"({mime_query}) and trashed=false" # and 'root' in parents"
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()
    files = results.get('files', [])
    print(f"Found {len(files)} files to process.")
    category_to_files, existing_folders = batch_categorize_files(files)
    batch_move_files(category_to_files, existing_folders)

if __name__ == "__main__":
    print("Starting Drive categorization...")
    process_all_drive_files()
    existing_folders = get_existing_folders()
    merge_and_cleanup_folders(existing_folders, cutoff=0.4)
    remove_empty_folders()
    print("Done.")