from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parent.parent
FIREBASE_FILE = BASE_DIR / "credentials" / "firebase.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(str(FIREBASE_FILE))
    firebase_admin.initialize_app(cred)

db = firestore.client()