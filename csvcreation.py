import os
import subprocess
import requests
import re
import json
import time
from dotenv import load_dotenv

load_dotenv()

ENSEMBLE_API_KEY = os.getenv("ENSEMBLE_API_KEY")
ENSEMBLE_ROOT = os.getenv("ENSEMBLE_ROOT")

def get_platform(url):
    if "tiktok.com" in url:
        return "tiktok"
    if "instagram.com" in url:
        return "instagram"
    return None

def get_content_type(url):
    if "tiktok.com" in url and "/video/" in url:
        return "video"
    if "instagram.com" in url and "/p/" in url:
        return "post"
    return None

def fetch_video_data(url):
    platform = get_platform(url) 
    content_type = get_content_type(url)
    
    if not platform or not content_type:
        return {"error": "Unsupported platform or content type."}
    
    return fetch_tiktok_data(url) if platform == "tiktok" else fetch_instagram_data(url)

def fetch_tiktok_data(url):
    response = requests.get(f"{ENSEMBLE_ROOT}/tt/post/info", params={"url": url, "token": ENSEMBLE_API_KEY})
    return handle_response(response)

def fetch_instagram_data(url):
    video_id = extract_instagram_video_id(url)
    if not video_id:
        return {"error": "Could not extract Instagram video ID."}
    
    response = requests.get(
        f"{ENSEMBLE_ROOT}/instagram/post/details",
        params={"code": video_id, "n_comments_to_fetch": 0, "token": ENSEMBLE_API_KEY}
    )
    return handle_response(response)

def handle_response(response):
    try:
        return response.json() if response.status_code == 200 else {"error": f"Failed: {response.status_code}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response."}

def extract_instagram_video_id(url):
    match = re.search(r"instagram\.com/p/([\w-]+)", url)
    return match.group(1) if match else None

def save_as_json(data, filename):
    if "error" in data:
        print(f"Error: {data['error']}")
        return
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")
    
    wait_for_file(filename)

    run_retrieve_info_script()

def wait_for_file(filename):
    while not os.path.exists(filename) or os.path.getsize(filename) == 0:
        time.sleep(1)  

def run_retrieve_info_script():
    try:
        subprocess.run(["python", "retrieveInfo.py"], check=True)
        print("retrieveInfo.py executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing retrieveInfo.py: {e}")

def main():
    url = input("Enter a TikTok or Instagram video URL: ")
    data = fetch_video_data(url)
    
    if "error" not in data:
        save_as_json(data, f"{get_platform(url)}_data.json")
    else:
        print(f"Error: {data['error']}")

if __name__ == "__main__":
    main()