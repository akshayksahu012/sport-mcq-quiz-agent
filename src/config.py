import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Centralized configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("[WARNING]: API Key is missing. Check your .env file setup!")