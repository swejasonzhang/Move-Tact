import json
import csv
import os
import subprocess

def extract_instagram_metrics(data):
    post = data.get("data", {})
    owner = post.get("owner", {})
    caption = post.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "") if post.get("edge_media_to_caption") else ""
    
    return {
        "id": post.get("id"),
        "shortcode": post.get("shortcode"),
        "is_video": post.get("is_video"),
        "likes": post.get("edge_media_preview_like", {}).get("count", 0),
        "comments": post.get("edge_media_preview_comment", {}).get("count", 0),
        "views": post.get("video_view_count") if post.get("is_video") else None,
        "caption": caption,
        "owner_username": owner.get("username"),
        "owner_full_name": owner.get("full_name"),
        "owner_is_verified": owner.get("is_verified"),
        "thumbnail_url": post.get("thumbnail_src"),
        "display_url": post.get("display_url"),
        "timestamp": post.get("taken_at_timestamp"),
        "shares": None,
        "audio_url": post.get("clips_music_attribution_info", {}).get("audio_url", ""),
        "audio_title": post.get("clips_music_attribution_info", {}).get("song_name", ""),
        "audio_artist": post.get("clips_music_attribution_info", {}).get("artist_name", "")
    }

def extract_tiktok_metrics(data, music_data=None):
    video = data.get("data", [{}])[0]
    music = video.get("music", {})

    return {
        "id": video.get("aweme_id"),
        "description": video.get("desc", ""),
        "likes": video.get("statistics", {}).get("digg_count", 0),
        "comments": video.get("statistics", {}).get("comment_count", 0),
        "views": video.get("statistics", {}).get("play_count", 0),
        "shares": video.get("statistics", {}).get("share_count", 0),
        "reposts": video.get("statistics", {}).get("repost_count", 0),
        "music_title": music.get("title", ""),
        "music_artist": music.get("author", ""),
        "song_link": music.get("play_url", {}).get("uri", ""),
        "song_id": music.get("id", ""),
        "sound_id": music.get("mid", ""),
        "ugc": music_data.get("video_count") if music_data else None,
        "owner_username": video.get("author", {}).get("unique_id", ""),
        "owner_nickname": video.get("author", {}).get("nickname", ""),
        "owner_verified": video.get("author", {}).get("verification_type", 0) == 1,
        "video_url": video.get("video", {}).get("play_addr", {}).get("url_list", [None])[0],
        "thumbnail_url": video.get("video", {}).get("cover", {}).get("url_list", [None])[0],
        "timestamp": video.get("create_time")
    }

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return None

def save_to_csv(filepath, headers, data):
    with open(filepath, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerow(data)

def process_instagram_data():
    data = load_json("./instagram_data.json")
    if not data:
        return

    metrics = extract_instagram_metrics(data)
    headers = [
        "id", "shortcode", "is_video", "likes", "comments", "views",
        "caption", "owner_username", "owner_full_name", "owner_is_verified",
        "thumbnail_url", "display_url", "timestamp", "shares",
        "audio_url", "audio_title", "audio_artist"
    ]
    save_to_csv("instagram_metrics.csv", headers, metrics)
    os.remove("./instagram_data.json")

def process_tiktok_data():
    data = load_json("./tiktok_data.json")
    music_data = load_json("./music_data.json")
    if not data:
        return

    metrics = extract_tiktok_metrics(data, music_data)
    headers = [
        "id", "description", "likes", "comments", "views", "shares",
        "reposts", "music_title", "music_artist", "song_link", "song_id",
        "sound_id", "ugc", "owner_username", "owner_nickname",
        "owner_verified", "video_url", "thumbnail_url", "timestamp"
    ]
    save_to_csv("tiktok_metrics.csv", headers, metrics)
    os.remove("./tiktok_data.json")
    if music_data:
        os.remove("./music_data.json")

def main():
    process_instagram_data()
    process_tiktok_data()
    run_upload_sheet_script()

def run_upload_sheet_script():
    try:
        subprocess.run(["python", "uploadSheets.py"], check=True)
    except subprocess.CalledProcessError as e:
        pass

if __name__ == "__main__":
    main()