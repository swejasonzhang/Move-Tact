import os
from dotenv import load_dotenv
import requests
import re
import json

load_dotenv()

ENSEMBLE_API_KEY = os.getenv("ENSEMBLE_API_KEY")
ENSEMBLE_ROOT = os.getenv("ENSEMBLE_ROOT")

# Function to determine platform (TikTok or Instagram)
def get_platform(url):
    if "tiktok.com" in url:
        return "tiktok"
    elif "instagram.com" in url:
        return "instagram"
    return None

# Function to determine content type (post, slideshow, or reel)
def get_content_type(url):
    if "tiktok.com" in url:
        if "/video/" in url:
            return "post"
        elif "/slideshow/" in url:
            return "slideshow"
    elif "instagram.com" in url:
        if "/reel/" in url:
            return "reel"
        elif "/p/" in url:
            return "post"
    return None

# Function to fetch video data (TikTok or Instagram)
def fetch_video_data(url):
    platform = get_platform(url)
    content_type = get_content_type(url)
    
    if not platform or not content_type:
        print("Unsupported platform or content type.")
        return None
    
    headers = {"Authorization": f"Bearer {ENSEMBLE_API_KEY}"}
    params = {"url": url, "token": ENSEMBLE_API_KEY}
    
    if platform == "tiktok":
        video_id = extract_tiktok_video_id(url)
        if not video_id:
            print("Could not extract TikTok video ID.")
            return None
        params["id"] = video_id
        if content_type == "post":
            endpoint = "/tt/post/info"
        elif content_type == "slideshow":
            endpoint = "/tt/slideshow/info"
    elif platform == "instagram":
        video_id = extract_instagram_video_id(url)
        if not video_id:
            print("Could not extract Instagram video ID.")
            return None
        params["id"] = video_id
        if content_type == "post":
            endpoint = "/ig/post/info"
        elif content_type == "reel":
            endpoint = "/ig/reel/info"
    else:
        print("Unsupported platform.")
        return None
    
    print(f"Fetching data for URL: {url}")
    response = requests.get(f"{ENSEMBLE_ROOT}{endpoint}", headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch video metadata: {response.json()}")
        return None

# Function to extract TikTok video ID
def extract_tiktok_video_id(url):
    match = re.search(r"tiktok.com/@[\w-]+/(video|slideshow)/(\d+)", url)
    if match:
        return match.group(2)
    return None

# Function to extract Instagram video ID
def extract_instagram_video_id(url):
    match = re.search(r"instagram\.com/(reels|p)/([\w-]+)", url)
    if match:
        return match.group(2)
    return None

# Function to save data as a JSON file
def save_as_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

# Main function to handle user input and fetch data
def main():
    video_url = input("Enter a TikTok or Instagram video URL: ")
    video_data = fetch_video_data(video_url)
    
    if video_data:
        platform = get_platform(video_url)
        content_type = get_content_type(video_url)
        filename = f"{platform}_{content_type}_data.json"
        save_as_json(video_data, filename)
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()