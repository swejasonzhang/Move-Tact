import json
import csv
import os

def extract_instagram_metrics(data):
    post_data = data.get("data", {})

    metrics = {
        "id": post_data.get("id"),
        "shortcode": post_data.get("shortcode"),
        "is_video": post_data.get("is_video"),
        "likes": post_data.get("edge_media_preview_like", {}).get("count", 0),
        "comments": post_data.get("edge_media_preview_comment", {}).get("count", 0),
        "views": post_data.get("video_view_count") if post_data.get("is_video") else None,
        "caption": post_data.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
        "owner": {
            "username": post_data.get("owner", {}).get("username"),
            "full_name": post_data.get("owner", {}).get("full_name"),
            "is_verified": post_data.get("owner", {}).get("is_verified"),
        },
        "thumbnail_url": post_data.get("thumbnail_src"),
        "display_url": post_data.get("display_url"),
        "timestamp": post_data.get("taken_at_timestamp"),
        "shares": None,
        "audio_url": post_data.get("clips_music_attribution_info", {}).get("audio_url", ""),
        "audio_title": post_data.get("clips_music_attribution_info", {}).get("song_name", ""),
        "audio_artist": post_data.get("clips_music_attribution_info", {}).get("artist_name", ""),
    }

    return metrics

def extract_tiktok_metrics(data):
    video_data = data.get("data", [])[0]
    music = video_data.get("music", {})
    song_url = music.get("play_url", {}).get("uri", "")

    metrics = {
        "id": video_data.get("aweme_id"),
        "description": video_data.get("desc", ""),
        "likes": video_data.get("statistics", {}).get("digg_count", 0),
        "comments": video_data.get("statistics", {}).get("comment_count", 0),
        "views": video_data.get("statistics", {}).get("play_count", 0),
        "shares": video_data.get("statistics", {}).get("share_count", 0),
        "reposts": video_data.get("statistics", {}).get("repost_count", 0),
        "music": {
            "title": music.get("title", ""),
            "artist": music.get("author", ""),
            "song_link": song_url,
            "song_id": music.get("id", ""),
            "sound_id": music.get("mid", ""),
            "ugc": int(video_data.get("ugc_count", 0)) if video_data.get("ugc_count", '0').isdigit() and int(video_data.get("ugc_count", 0)) > 0 else None,
        },
        "owner": {
            "username": video_data.get("author", {}).get("unique_id", ""),
            "nickname": video_data.get("author", {}).get("nickname", ""),
            "verified": video_data.get("author", {}).get("verification_type", 0) == 1,
        },
        "video_url": video_data.get("video", {}).get("play_addr", {}).get("url_list", [None])[0],
        "thumbnail_url": video_data.get("video", {}).get("cover", {}).get("url_list", [None])[0],
        "timestamp": video_data.get("create_time"),
    }

    return metrics

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return None

instagram_data = load_json_file("./instagram_data.json")
if instagram_data:
    instagram_metrics = extract_instagram_metrics(instagram_data)
    instagram_csv_file_path = "instagram_metrics.csv"
    instagram_header = [
        "id", "shortcode", "is_video", "likes", "comments", "views", 
        "caption", "owner_username", "owner_full_name", "owner_is_verified", 
        "thumbnail_url", "display_url", "timestamp", "shares", 
        "audio_url", "audio_title", "audio_artist"
    ]

    with open(instagram_csv_file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=instagram_header)
        writer.writeheader()
        instagram_metrics["owner_username"] = instagram_metrics["owner"].get("username")
        instagram_metrics["owner_full_name"] = instagram_metrics["owner"].get("full_name")
        instagram_metrics["owner_is_verified"] = instagram_metrics["owner"].get("is_verified")
        del instagram_metrics["owner"]
        writer.writerow(instagram_metrics)

    os.remove("./instagram_data.json")

tiktok_data = load_json_file("./tiktok_data.json")
if tiktok_data:
    tiktok_metrics = extract_tiktok_metrics(tiktok_data)
    tiktok_csv_file_path = "tiktok_metrics.csv"
    tiktok_header = [
        "id", "description", "likes", "comments", "views", "shares", 
        "reposts", "music_title", "music_artist", "song_link", "song_id", "sound_id", "ugc",
        "owner_username", "owner_nickname", "owner_verified", 
        "video_url", "thumbnail_url", "timestamp"
    ]

    with open(tiktok_csv_file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=tiktok_header)
        writer.writeheader()
        tiktok_metrics["music_title"] = tiktok_metrics["music"].get("title")
        tiktok_metrics["music_artist"] = tiktok_metrics["music"].get("artist")
        tiktok_metrics["song_link"] = tiktok_metrics["music"].get("song_link")
        tiktok_metrics["song_id"] = tiktok_metrics["music"].get("song_id")
        tiktok_metrics["sound_id"] = tiktok_metrics["music"].get("sound_id")
        tiktok_metrics["ugc"] = tiktok_metrics["music"].get("ugc")
        del tiktok_metrics["music"]
        tiktok_metrics["owner_username"] = tiktok_metrics["owner"].get("username")
        tiktok_metrics["owner_nickname"] = tiktok_metrics["owner"].get("nickname")
        tiktok_metrics["owner_verified"] = tiktok_metrics["owner"].get("verified")
        del tiktok_metrics["owner"]
        writer.writerow(tiktok_metrics)

    os.remove("./tiktok_data.json")