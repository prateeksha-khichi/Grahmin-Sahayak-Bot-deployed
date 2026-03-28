import os
import gdown

# The exact model file causing size issues
MODEL_DIR = "models/loan_eligibility"
MODEL_PATH = os.path.join(MODEL_DIR, "loan_eligibility_model.pkl")

# We use an environment variable so you can set this in Railway's dashboard securely.
# To get this ID: Share the Google Drive file -> "Anyone with the link" -> Copy the ID from the link.
# Hardcoded as fallback — no env variable needed!
GDRIVE_FILE_ID = os.getenv("GOOGLE_DRIVE_MODEL_ID", "11TiSpJTC493sAnm0xuooaDc5hGzej6Js")

def download_model():
    print("="*50)
    print("🤖 Checking ML Model Status...")
    print("="*50)
    
    if os.path.exists(MODEL_PATH):
        file_size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        print(f"✅ Model already exists locally at {MODEL_PATH} ({file_size_mb:.2f} MB). Skipping download.")
        return

    print(f"📥 Model NOT found at {MODEL_PATH}. Downloading from Google Drive...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    if GDRIVE_FILE_ID == "YOUR_GOOGLE_DRIVE_FILE_ID_HERE":
        print("❌ ERROR: GOOGLE_DRIVE_MODEL_ID is not set in environment variables.")
        print("Please add the Google Drive file ID to your Railway variables.")
        return

    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    
    try:
        # gdown allows downloading large files from Google Drive easily
        gdown.download(url, MODEL_PATH, quiet=False)
        if os.path.exists(MODEL_PATH):
            print("✅ Model downloaded successfully!")
        else:
            print("❌ Download failed. File not created.")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")

if __name__ == "__main__":
    download_model()
