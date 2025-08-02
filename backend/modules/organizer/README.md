# Google Drive Organizer with Gemini AI

This module automatically categorizes and organizes files in your Google Drive using Google Gemini AI for content analysis. It creates or merges folders based on content similarity and can remove empty or duplicate folders.

## Features

- **Automatic categorization:** Uses Gemini AI to suggest categories for your files.
- **Dynamic folder management:** Creates new folders for new categories, merges similar folders, and removes empty ones.
- **Batch processing:** Processes all supported files in your Drive in one go.
- **OCR support:** Extracts text from images and PDFs using Tesseract OCR.
- **File type support:** Handles PDF, DOCX, and image files.
- **Environment variable management:** Uses a `.env` file for sensitive information like API keys.
- **Google Drive integration:** Uses Google Drive API for file and folder management.

## Requirements

- **Google Drive API credentials:**  
  - Download your `credentials.json` from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
  - Place it in the same directory as the scripts.
- **Gemini API Key:**  
  - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
  - Add it to a `.env` file as `GENAI_API_KEY=your_key_here`.

- **Python packages:**  
  - Install requirements with:

    ```bash
    pip install -r requirements.txt
    ```

  - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) must be installed and its path set in `file_utils.py`.

## Additional Requirements by File

Below are the extra Python packages you may need for specific files in this module:

### `file_utils.py`

- **pdfplumber** (for PDF text extraction)
- **python-docx** (for DOCX text extraction)
- **pillow** (for image processing)
- **pytesseract** (for OCR)

Install with:

### `genai_client.py`

- **python-dotenv** (for loading environment variables)
- **google-generativeai** (for Gemini API access)

Install with:

### `drive_auth.py`, `folder_utils.py`, `file_utils.py`, `categorizer.py`

- **google-api-python-client**
- **google-auth**
- **google-auth-oauthlib**

Install with:

### System Requirements

- **Tesseract OCR** must be installed on your system for OCR to work.  
  Download from: <https://github.com/tesseract-ocr/tesseract>
- Ensure the Tesseract executable path is correctly set in `file_utils.py`.

## Setup

1. **Credentials:**
   - Place your `credentials.json` in the module directory.
   - The script will generate a `token.json` on first run for authentication.

2. **Gemini API Key:**

- Create a `.env` file in the module directory:

```bash
GENAI_API_KEY=your_gemini_api_key_here
```

3. **Tesseract OCR:**

   - Install Tesseract and ensure the path in `file_utils.py` matches your installation.

## Usage

1. **Run the categorizer:**

2. **What happens:**

```bash
# Navigate to the module directory
cd categorizer/ && uvicorn main:app --reload
```

- This will start the categorization process for all files in your Google Drive.
- The script will authenticate with Google Drive.
- It will scan your Drive for supported files (PDF, DOCX, images).
- Each file is analyzed and categorized using Gemini AI.
- Files are moved to the appropriate folders (created or merged as needed).
- Duplicate and empty folders are cleaned up.

## File Structure

- `main.py` — Main script to run the categorization process.
- `requirements.txt` — List of required Python packages.
- `categorizer.py` - Main categorization logic.
- `config.py` — Configuration settings for the module.
- `drive_auth.py` — Handles Google Drive authentication.
- `drive_files.py` - Function for listing Google Drive files.
- `genai_client.py` — Handles Gemini API client.
- `file_utils.py` — File download, OCR, and content extraction.
- `folder_utils.py` — Folder management, merging, and cleanup.
- `categorization.py` — AI categorization logic.

## Notes

- **Quota:** The Gemini API has daily and rate limits. If you hit a quota, the script will notify you.
- **Safety:** The script moves and deletes folders/files. Test on a non-critical Drive account first.
- **Customization:** You can adjust the folder similarity cutoff in `categorizer.py` (`merge_and_cleanup_folders(existing_folders, cutoff=0.3)`).

## Troubleshooting

- **Quota errors:** Wait for your Gemini quota to reset or upgrade your plan.
- **Authentication errors:** Delete `token.json` and re-run to re-authenticate.
- **Tesseract errors:** Ensure Tesseract is installed and the path is correct.

## License

MIT
