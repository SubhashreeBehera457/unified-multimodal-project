import os
from huggingface_hub import HfApi

# Load from environment variable. Set HF_TOKEN in your .env file.
# See .env.example for instructions. NEVER hardcode API tokens.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise SystemExit(
        "ERROR: HF_TOKEN environment variable not set.\n"
        "Copy .env.example to .env and add your HuggingFace token."
    )

# Update this path to match your local project directory
FOLDER_PATH = os.environ.get("PROJECT_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

api = HfApi(token=TOKEN)
try:
    # Get username
    user_info = api.whoami()
    username = user_info["name"]
    print(f"Logged in as: {username}")
    
    repo_id = f"{username}/Unified-Disaster-Management-System"
    print(f"Creating/Checking repository: {repo_id}")
    
    # Create space if it doesn't exist
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True
    )
    
    print("Uploading files to Hugging Face Spaces...")
    api.upload_folder(
        folder_path=FOLDER_PATH,
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=[
            ".git/*",
            "__pycache__/*",
            "*.pkl", 
            "results_misinfo/*"
        ]
    )
    
    print(f"Deploy successful! Live at: https://huggingface.co/spaces/{repo_id}")
except Exception as e:
    print(f"An error occurred: {e}")
