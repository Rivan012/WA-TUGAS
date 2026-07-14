from dotenv import load_dotenv
import os

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
FIREBASE_CREDENTIAL = os.getenv("FIREBASE_CREDENTIAL")
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
