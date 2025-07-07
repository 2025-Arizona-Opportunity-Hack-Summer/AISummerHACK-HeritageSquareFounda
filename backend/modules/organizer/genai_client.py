from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
def genai_client():

    GENAI_API_KEY = os.getenv("GENAI_API_KEY")

    if not GENAI_API_KEY:
        raise ValueError("GENAI_API_KEY not found in environment variables. Please set it in your .env file.")

    client = genai.Client(api_key=GENAI_API_KEY)

    return client