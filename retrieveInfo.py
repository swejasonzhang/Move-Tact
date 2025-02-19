import os
import subprocess
import requests
import re
import json
import time
from bs4 import BeautifulSoup
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
    if "tiktok.com" in url:
        return "video" if "/video/" in url else "photo" if "/photo/" in url else None
    if "instagram.com" in url:
        return "post" if "/p/" in url else "reel" if "/reels/" in url else None
    return None

def clean_music_title(title):
    return title.replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('!', '').replace('.', '')

def fetch_video_data(url):
    platform = get_platform(url) 
    content_type = get_content_type(url)
    
    if not platform or not content_type:
        return {"error": "Unsupported platform or content type."}
    
    if platform == "tiktok":
        return fetch_tiktok_video_data(url) if content_type == "video" else fetch_tiktok_photo_data(url)
    elif platform == "instagram":
        return fetch_instagram_post_data(url) if content_type == "post" else fetch_instagram_reel_data(url)

def fetch_tiktok_video_data(url):
    response = requests.get(f"{ENSEMBLE_ROOT}/tt/post/info", params={"url": url, "token": ENSEMBLE_API_KEY})
    data = response.json()
    
    if response.status_code == 200 and "data" in data and isinstance(data["data"], list) and data["data"]:
        video_data = data["data"][0]
        music_info = video_data.get("added_sound_music_info", {})
        music_id = music_info.get("id")
        music_title = music_info.get("title", "Unknown Title")

        if music_id:
            music_title_clean = clean_music_title(music_title)
            music_url = f"https://www.tiktok.com/music/{music_title_clean}-{music_id}"
            print(f"Music URL: {music_url}")
            
            user_count_data = get_user_count_from_music_url(music_url)
            
            if user_count_data and "view_count" in user_count_data:
                video_data["ugc_count"] = user_count_data["view_count"]
                video_data["music_title"] = music_title
                video_data["song_link"] = music_url

        return data
    return {"error": f"Failed to fetch TikTok video data: {data.get('error', 'Unknown error')}"}

def fetch_tiktok_photo_data(url):
    modified_url = url.replace("/photo/", "/video/")
    response = requests.get(f"{ENSEMBLE_ROOT}/tt/post/info", params={"url": modified_url, "token": ENSEMBLE_API_KEY})
    return handle_response(response)

def fetch_instagram_post_data(url):
    post_id = extract_instagram_id(url, "p")
    if not post_id:
        return {"error": "Could not extract Instagram post ID."}
    
    response = requests.get(
        f"{ENSEMBLE_ROOT}/instagram/post/details",
        params={"code": post_id, "n_comments_to_fetch": 0, "token": ENSEMBLE_API_KEY}
    )
    return handle_response(response)

def fetch_instagram_reel_data(url):
    reel_id = extract_instagram_id(url, "reel") or extract_instagram_id(url, "reels")
    if not reel_id:
        return {"error": "Could not extract Instagram reel ID."}
    
    response = requests.get(
        f"{ENSEMBLE_ROOT}/instagram/post/details",
        params={"code": reel_id, "n_comments_to_fetch": 0, "token": ENSEMBLE_API_KEY}
    )
    
    return handle_response(response)

def handle_response(response):
    try:
        return response.json() if response.status_code == 200 else {"error": f"Failed: {response.status_code}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response."}

def extract_instagram_id(url, content_type):
    match = re.search(rf"instagram\.com/{content_type}/([\w-]+)", url)
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
    print(f"{filename} is ready.")

def run_retrieve_info_script():
    try:
        subprocess.run(["python", "csvcreation.py"], check=True)
        print("retrieveInfo.py executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing retrieveInfo.py: {e}")

def get_user_count_from_music_url(music_url):
    # Send a GET request to the music URL
    response = requests.get(music_url)
    
    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Parse the response as HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the <h2> element with the specified data-e2e attribute and title="views"
            view_count_element = soup.find('h2', {'data-e2e': 'music-video-count', 'title': 'views'})
            
            print(view_count_element)
            
            # Check if the element was found
            if view_count_element:
                # Extract the text content (view count)
                view_count = view_count_element.text.strip()
            else:
                view_count = "Not found"
            
            # Extract just the song name and ID
            music_url_parts = music_url.split('-')
            song_name = '-'.join(music_url_parts[:-1])  # Everything except the last part
            music_id = music_url_parts[-1]  # The last part is the ID
            
            print(song_name)
            
            # Rebuild the music URL without the author part
            cleaned_music_url = f"{song_name}-{music_id}"
            
            # Construct a JSON object with the extracted view count
            data = {
                'url': cleaned_music_url,
                'view_count': view_count
            }
            
            # Save the response data into a JSON file
            with open('music_data.json', 'w') as json_file:
                json.dump(data, json_file, indent=4)  # Pretty-print JSON
            
            print("Data saved to music_data.json")
            return data  # Return the parsed data if needed
        
        except Exception as e:
            print(f"Error while parsing HTML: {e}")
            return None
    else:
        print(f"Error: Received status code {response.status_code}.")
        return None

def main():
    url = input("Enter a TikTok or Instagram video URL: ")
    data = fetch_video_data(url)
    
    if "error" not in data:
        save_as_json(data, f"{get_platform(url)}_data.json")
    else:
        print(f"Error: {data['error']}")

if __name__ == "__main__":
    main()