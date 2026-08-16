from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file
def get_openai_api_key() -> str:
    """Retrieve the OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")
    return api_key