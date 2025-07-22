# Organizer Module

This module automatically categorizes and organizes files in your Google Drive using Google Gemini AI for content analysis. It creates or merges folders based on content similarity and can remove empty or duplicate folders.

## Features

- **Automatic categorization:** Uses Gemini AI to suggest categories for your files.
- **Dynamic folder management:** Creates new folders for new categories, merges similar folders, and removes empty ones.
- **Batch processing:** Processes all supported files in your Drive in one go.

## Requirements
- **Gemini API Key:**  
  - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
  - Add it to a `.env` file as `GENAI_API_KEY=your_key_here`.

- **Python packages:**  
  - Install requirements with:
    ```bash
    pip install python-dotenv genai difflib PIL
    ```
    ```
## Additional Requirements by File

Below are the extra Python packages you may need for specific files in this module:

### `genai_client.py`

- **python-dotenv** (for loading environment variables)
- **google-generativeai** (for Gemini API access)

## Usage

1. **Run the categorizer:**
  ```bash
  python categorizer.py
  ```
2. **What happens:**
- This will start the categorization process for all files in your Google Drive.
- The script will authenticate with Google Drive.
- It will scan your Drive for supported files (PDF, DOCX, images).
- Each file is analyzed and categorized using Gemini AI.
- Files are moved to the appropriate folders (created or merged as needed).
- Duplicate and empty folders are cleaned up.

## File Structure

- `categorizer.py` — Main entry point.
- `genai_client.py` — Handles Gemini API client.
- `folder_utils.py` — Folder management, merging, and cleanup.
- `categorization.py` — AI categorization logic.

## Notes
- **Quota:** The Gemini API has daily and rate limits. If you hit a quota, the script will notify you.
- **Safety:** The script moves and deletes folders/files. Test on a non-critical Drive account first.
- **Customization:** You can adjust the folder similarity cutoff in `categorizer.py` (`merge_and_cleanup_folders(existing_folders, cutoff=0.3)`).

## Troubleshooting

- **Quota errors:** Wait for your Gemini quota to reset or upgrade your plan.
- **Authentication errors:** Delete `token.json` and re-run to re-authenticate.

## License

MIT
