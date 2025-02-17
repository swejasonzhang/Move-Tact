import json
import csv
import os

# Function to extract Instagram metrics
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
    }

    return metrics

# Function to extract TikTok metrics
def extract_tiktok_metrics(data):
    video_data = data.get("data", [])[0]

    metrics = {
        "id": video_data.get("aweme_id"),
        "description": video_data.get("desc", ""),
        "likes": video_data.get("statistics", {}).get("digg_count", 0),
        "comments": video_data.get("statistics", {}).get("comment_count", 0),
        "views": video_data.get("statistics", {}).get("play_count", 0),
        "shares": video_data.get("statistics", {}).get("share_count", 0),
        "reposts": video_data.get("statistics", {}).get("repost_count", 0),
        "music": {
            "title": video_data.get("music", {}).get("title", ""),
            "artist": video_data.get("music", {}).get("author", ""),
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

# Function to load JSON data if the file exists
def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    else:
        print(f"File {filename} does not exist.")
        return None

# Load Instagram data from file
instagram_data = load_json_file("./instagram_data.json")
if instagram_data:
    # Extract Instagram metrics
    instagram_metrics = extract_instagram_metrics(instagram_data)

    # Write Instagram metrics to CSV
    instagram_csv_file_path = "instagram_metrics.csv"
    instagram_header = [
        "id", "shortcode", "is_video", "likes", "comments", "views", 
        "caption", "owner_username", "owner_full_name", "owner_is_verified", 
        "thumbnail_url", "display_url", "timestamp", "shares"
    ]

    with open(instagram_csv_file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=instagram_header)
        writer.writeheader()
        instagram_metrics["owner_username"] = instagram_metrics["owner"].get("username")
        instagram_metrics["owner_full_name"] = instagram_metrics["owner"].get("full_name")
        instagram_metrics["owner_is_verified"] = instagram_metrics["owner"].get("is_verified")
        del instagram_metrics["owner"]  # Remove nested "owner" dict
        writer.writerow(instagram_metrics)

    print("Instagram metrics have been written to CSV file.")

    # Delete the Instagram JSON file after processing
    os.remove("./instagram_data.json")
    print("Instagram JSON file has been deleted.")

# Load TikTok data from file
tiktok_data = load_json_file("./tiktok_data.json")
if tiktok_data:
    # Extract TikTok metrics
    tiktok_metrics = extract_tiktok_metrics(tiktok_data)

    # Write TikTok metrics to CSV
    tiktok_csv_file_path = "tiktok_metrics.csv"
    tiktok_header = [
        "id", "description", "likes", "comments", "views", "shares", 
        "reposts", "music_title", "music_artist", 
        "owner_username", "owner_nickname", "owner_verified", 
        "video_url", "thumbnail_url", "timestamp"
    ]

    with open(tiktok_csv_file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=tiktok_header)
        writer.writeheader()
        tiktok_metrics["music_title"] = tiktok_metrics["music"].get("title")
        tiktok_metrics["music_artist"] = tiktok_metrics["music"].get("artist")
        del tiktok_metrics["music"]  # Remove nested "music" dict
        tiktok_metrics["owner_username"] = tiktok_metrics["owner"].get("username")
        tiktok_metrics["owner_nickname"] = tiktok_metrics["owner"].get("nickname")
        tiktok_metrics["owner_verified"] = tiktok_metrics["owner"].get("verified")
        del tiktok_metrics["owner"]  # Remove nested "owner" dict
        writer.writerow(tiktok_metrics)

    print("TikTok metrics have been written to CSV file.")

    # Delete the TikTok JSON file after processing
    os.remove("./tiktok_data.json")
    print("TikTok JSON file has been deleted.")
