import os
from dotenv import load_dotenv
import requests
import re
from retrieveInfo import retrieveInfo 

load_dotenv()

ENSEMBLE_API_KEY = os.getenv("ENSEMBLE_API_KEY")
ENSEMBLE_ROOT = os.getenv("ENSEMBLE_ROOT")

# Function to determine platform (YouTube or TikTok)
def get_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "tiktok.com" in url:
        return "tiktok"
    return None

# Function to fetch video data (YouTube or TikTok)
def fetch_video_data(url):
    platform = get_platform(url)
    if not platform:
        print("Unsupported platform.")
        return None
    
    headers = {"Authorization": f"Bearer {ENSEMBLE_API_KEY}"}
    params = {"url": url, "token": ENSEMBLE_API_KEY}
    
    if platform == "youtube":
        video_id = extract_youtube_video_id(url)
        if not video_id:
            print("Could not extract YouTube video ID.")
            return None
        params["id"] = video_id
        endpoint = "/youtube/channel/get-short-stats"
    elif platform == "tiktok":
        endpoint = "/tt/post/info"
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

# Function to extract YouTube video ID
def extract_youtube_video_id(url):
    match = re.search(r"(?<=v=)[\w-]+", url)
    if match:
        return match.group(0)
    return None

# Example of fetching video data and passing it to the OpenAI function
def main():
    video_url = input("Enter a YouTube or TikTok video URL: ")
    video_data = fetch_video_data(video_url)
    
    if video_data:
        # Pass the fetched data directly to your OpenAI function
        response_from_openai = retrieveInfo(video_data)
        
        # Print the response from OpenAI
        print("Response from OpenAI:", response_from_openai)

if __name__ == "__main__":
    main()