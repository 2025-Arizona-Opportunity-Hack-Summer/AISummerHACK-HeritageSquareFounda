from modules.organizer.genai_client import genai_client
from modules.organizer.file_utils import download_file_content, extract_text_from_image
from modules.organizer.folder_utils import get_existing_folders
import re
from PIL import Image
from google import genai

client = genai_client()

ALLOWED_CATEGORIES = {
    "Curation", "Employee Resources", "Images", "Interviews", "Research", "Restoration"
}

def categorize_image_with_genai_vision(file_data):
    try:
        file_data.seek(0)
        try:
            img = Image.open(file_data)
            img.verify()
        except Exception as imgae:
            print(f"Image verification failed: {imgae}")
            return "Uncategorized"
        file_data.seek(0)
        prompt = (
            "Categorize the image based on its content. Choose only from the following:\n"
            "Curation, Employee Resources, Images, Interviews, Research, Restoration.\n"
            "Reply in the format:\n**Category:** <category>"
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

def categorize_and_tag_geminiai(text):
    try:
        prompt = (
            "Categorize the following document into one of the following categories only:\n"
            "Curation, Employee Resources, Images, Interviews, Research, Restoration.\n\n"
            "Reply in the format:\n**Category:** <category>\n\n"
            f"Text:\n{text}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )
        return response
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            print("Gemini API quota exceeded. Please wait or upgrade your plan.")
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

            # Check against allowed categories
            if category in ALLOWED_CATEGORIES:
                print(f"Extracted category: {category}")
                return category
            else:
                print(f"Invalid category received: {category}")
                return "Uncategorized"
    except Exception as e:
        print(f"Error extracting category: {e}")
    return "Uncategorized"

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
