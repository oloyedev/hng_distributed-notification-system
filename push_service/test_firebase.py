import firebase_admin
from firebase_admin import credentials
import os

try:
    # Check if credentials file exists
    cred_path = "firebase-credentials.json"
    if not os.path.exists(cred_path):
        print("❌ ERROR: firebase-credentials.json not found!")
        exit(1)
    
    # Initialize Firebase
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    
    print("✅ SUCCESS: Firebase initialized successfully!")
    print(f"✅ Project ID: {cred.project_id}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
