import os
import firebase_admin
from firebase_admin import credentials, storage
from datetime import timedelta
from fastapi import HTTPException

# Initialize Firebase App
# Ensure GOOGLE_APPLICATION_CREDENTIALS points to your json file
# or the environment is configured on Cloud Run.

try:
    if not firebase_admin._apps:
        # Check if credential file exists, otherwise assume implicit environment (Cloud Run)
        cred = credentials.ApplicationDefault() 
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
             cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'your-project.appspot.com')
        })
except Exception as e:
    print(f"Warning: Firebase initialization failed. Check credentials. {e}")

class MediaService:
    @staticmethod
    def generate_signed_url(user_id: str, filename: str, content_type: str):
        bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
        if not bucket_name:
             # Fallback for local testing without firebase configured
             return {
                 "upload_url": "http://localhost:fake-s3/upload",
                 "file_path": f"users/{user_id}/uploads/{filename}",
                 "note": "Firebase Bucket not configured"
             }

        try:
            bucket = storage.bucket()
            # Organize files by user
            blob_path = f"users/{user_id}/uploads/{filename}"
            blob = bucket.blob(blob_path)

            # Generate Signed URL (valid for 15 minutes)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type
            )
            
            return {
                "upload_url": url,
                "file_path": blob_path
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")
