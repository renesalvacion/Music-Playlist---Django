from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from pymongo import MongoClient
from googleapiclient.discovery import build
import json

# ------------------------------
# MongoDB setup
# ------------------------------
MONGO_URI = "mongodb+srv://jrsalvacion:jrsalvacion@cluster0.lizmpn8.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["music_db"]
collection = db["tracks"]

# ------------------------------
# YouTube API setup
# ------------------------------
YOUTUBE_API_KEY = "AIzaSyB2v2oSuiAbSB-zgB64ocFE5CPe3zRp6uI"

def search_youtube(title):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=title,
        part="snippet",
        type="video",
        maxResults=1
    )
    response = request.execute()
    if not response["items"]:
        return None

    video = response["items"][0]
    return {
        "video_id": video["id"]["videoId"],
        "title": video["snippet"]["title"],
        "thumbnail": video["snippet"]["thumbnails"]["high"]["url"]
    }

# ------------------------------
# Views
# ------------------------------

def index(request):
    playlist = list(collection.find({"validated": True}).sort("created_at", 1))
    return render(request, "index.html", {"playlist": playlist})


def add_music(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    title = request.POST.get("title", "").strip()
    if not title:
        return JsonResponse({"error": "Title is required"}, status=400)

    yt = search_youtube(title)
    if not yt:
        return JsonResponse({"error": "Music not found"}, status=404)

    video_title = yt["title"]
    if "-" in video_title:
        song_name, artist = map(str.strip, video_title.split("-", 1))
    else:
        song_name = video_title
        artist = "Unknown"

    data = {
        "song_name": song_name,
        "artist": artist,
        "youtube_video_id": yt["video_id"],
        "thumbnail": yt["thumbnail"],
        "validated": True,
        "created_at": datetime()
    }

    collection.insert_one(data)

    return JsonResponse({
        "track": {
            "song_name": song_name,
            "artist": artist,
            "youtube_video_id": yt["video_id"],
            "thumbnail": yt["thumbnail"]
        }
    })


def delete_music(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    video_id = data.get("youtube_video_id")

    collection.delete_one({"youtube_video_id": video_id})
    return JsonResponse({"success": True})
