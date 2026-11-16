import os
import subprocess
import sys

def install_kaggle():
    print("Installing Kaggle API...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle", "pandas", "numpy", "scikit-learn", "torch", "transformers", "shap"])

def download_datasets():
    print("\nChecking for Kaggle configuration...")
    # Standard location for kaggle.json on Windows
    kaggle_dir = os.path.expanduser("~/.kaggle")
    kaggle_json_path = os.path.join(kaggle_dir, "kaggle.json")
    
    if not os.path.exists(kaggle_json_path):
        print(f"ERROR: Could not find Kaggle API credentials at {kaggle_json_path}")
        print("Please follow these steps:")
        print("1. Go to https://www.kaggle.com/settings")
        print("2. Click 'Create New Token' to download kaggle.json")
        print(f"3. Place the downloaded file in: {kaggle_dir}")
        print("4. Run this script again.")
        return False
        
    print("Kaggle credentials found. Proceeding with downloads...")
    
    # Create data directories
    os.makedirs("data/tweets", exist_ok=True)
    os.makedirs("data/satellite", exist_ok=True)
    
    try:
        # Download Disaster Tweets Dataset (For Phase 2 NLP & Misinformation)
        print("\nDownloading Disaster Tweets Dataset...")
        subprocess.check_call(["kaggle", "competitions", "download", "-c", "nlp-getting-started", "-p", "data/tweets"])
        subprocess.check_call(["unzip", "-o", "data/tweets/nlp-getting-started.zip", "-d", "data/tweets/"])
        
        # Note: You can add more datasets here as needed
        # e.g., subprocess.check_call(["kaggle", "datasets", "download", "-d", "username/dataset-name", "-p", "data/satellite"])
        
        print("\nDatasets downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while downloading: {e}")
        return False

if __name__ == "__main__":
    install_kaggle()
    download_datasets()
