import os
import requests
from PIL import Image
from io import BytesIO

def download_images():
    print("Downloading sample real disaster images...")
    
    # We will use some public domain/creative commons sample image URLs for floods and collapsed buildings
    urls = {
        "SEVERE DAMAGE": [
            "https://upload.wikimedia.org/wikipedia/commons/4/41/FEMA_-_39800_-_Destroyed_homes_in_Texas.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/7/77/FEMA_-_43003_-_Debris_in_Texas.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/3/36/FEMA_-_43232_-_Damaged_home_in_Texas.jpg"
        ],
        "MILD DAMAGE": [
            "https://upload.wikimedia.org/wikipedia/commons/0/05/FEMA_-_41159_-_Flooded_streets_in_North_Dakota.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/e/e0/FEMA_-_42691_-_Flooded_homes_in_Texas.jpg"
        ],
        "NO DAMAGE": [
            "https://upload.wikimedia.org/wikipedia/commons/c/c5/Aerial_view_of_suburban_neighborhood.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/a/ae/Suburban_neighborhood.jpg"
        ]
    }
    
    os.makedirs("data/satellite_real/0_NO_DAMAGE", exist_ok=True)
    os.makedirs("data/satellite_real/1_MILD_DAMAGE", exist_ok=True)
    os.makedirs("data/satellite_real/2_SEVERE_DAMAGE", exist_ok=True)
    
    label_map = {"NO DAMAGE": 0, "MILD DAMAGE": 1, "SEVERE DAMAGE": 2}
    
    count = 0
    for label, url_list in urls.items():
        class_idx = label_map[label]
        dir_name = f"data/satellite_real/{class_idx}_{label.replace(' ', '_')}"
        for i, url in enumerate(url_list):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content)).convert('RGB')
                    img = img.resize((224, 224))
                    img.save(os.path.join(dir_name, f"img_{count}.jpg"))
                    count += 1
            except Exception as e:
                print(f"Failed to download {url}: {e}")
                
    print(f"Successfully downloaded {count} real images to data/satellite_real.")

if __name__ == "__main__":
    download_images()
