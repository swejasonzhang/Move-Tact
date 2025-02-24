import os
import subprocess
import requests
import re
import json
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
            video_count_data = get_video_count_from_music_url(music_url)
            
            if video_count_data and "video_count" in video_count_data:
                video_data["video_count"] = video_count_data["video_count"]
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
        return
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    wait_for_file(filename)
    run_retrieve_info_script()

def wait_for_file(filename):
    while not os.path.exists(filename) or os.path.getsize(filename) == 0:
        time.sleep(1)

def run_retrieve_info_script():
    try:
        subprocess.run(["python", "csvcreation.py"], check=True)
    except subprocess.CalledProcessError as e:
        pass

def get_video_count_from_music_url(music_url):
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(music_url)

        try:
            video_count_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[data-e2e="music-video-count"]'))
            )
            strong_tag = video_count_element.find_element(By.TAG_NAME, "strong")
            video_count = strong_tag.text.strip()
        except Exception as e:
            video_count = "Not found"

        data = {
            'url': music_url,
            'video_count': video_count
        }

        with open('music_data.json', 'w', encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)

        return data

    except Exception as e:
        return None
    finally:
        if driver:
            driver.quit()

def main():
    url = input("Enter a TikTok or Instagram video URL: ")
    data = fetch_video_data(url)
    
    if "error" not in data:
        filename = f"{get_platform(url)}_data.json"
        save_as_json(data, filename)
        run_csv_creation_script()

def run_csv_creation_script():
    try:
        subprocess.run(["python", "csvcreation.py"], check=True)
    except subprocess.CalledProcessError as e:
        pass

if __name__ == "__main__":
    main()