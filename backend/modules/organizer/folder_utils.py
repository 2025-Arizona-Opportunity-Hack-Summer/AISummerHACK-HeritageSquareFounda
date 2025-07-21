from modules.organizer.drive_auth import drive_auth
import difflib

drive_service = drive_auth()

def get_existing_folders():
    """Return a dict of {folder_name_lower: folder_id} for all folders in the Drive."""
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    return {folder['name'].strip().lower(): folder['id'] for folder in results.get('files', [])}

def find_best_folder_match(category, existing_folders, cutoff=0.4):
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
    best_match = find_best_folder_match(category, existing_folders)
    if best_match:
        print(f"Using existing folder: {best_match} for category: {category}")
        return existing_folders[best_match]
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

def batch_move_files(category_to_files, existing_folders):
    for category, file_ids in category_to_files.items():
        folder_id = ensure_folder(category, existing_folders)
        for file_id in file_ids:
            move_file_to_folder(file_id, folder_id, category)

def group_similar_folders(existing_folders, cutoff=0.6):
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
        canonical = min(matches, key=len)
        grouped.setdefault(canonical, [])
        for m in matches:
            if m != canonical:
                grouped[canonical].append(m)
                used.add(m)
        used.add(canonical)
    return grouped

def merge_and_cleanup_folders(existing_folders, cutoff=0.3):
    """
    Moves files from similar folders into a canonical folder and deletes duplicates.
    """
    grouped = group_similar_folders(existing_folders, cutoff)
    for canonical, duplicates in grouped.items():
        if canonical not in existing_folders:
            print(f"Canonical folder '{canonical}' no longer exists. Skipping group.")
            continue
        canonical_id = existing_folders[canonical]
        for dup_name in duplicates:
            if dup_name not in existing_folders:
                print(f"Duplicate folder '{dup_name}' no longer exists. Skipping.")
                continue
            dup_id = existing_folders[dup_name]
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
            drive_service.files().delete(fileId=dup_id).execute()
            print(f"Deleted duplicate folder: {dup_name}")
            del existing_folders[dup_name]

def remove_empty_folders():
    """Delete all empty folders in the Drive (not trashed)."""
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    print(f"Checking {len(folders)} folders for emptiness...")
    for folder in folders:
        children = drive_service.files().list(
            q=f"'{folder['id']}' in parents and trashed=false",
            fields="files(id)"
        ).execute()
        if not children.get('files'):
            print(f"Deleting empty folder: {folder['name']}")
            drive_service.files().delete(fileId=folder['id']).execute()