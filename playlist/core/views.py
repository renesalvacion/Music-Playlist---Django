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
db = client.get_database("music_db")
collection = db.get_collection("tracks")

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
# Django views
# ------------------------------

def index(request):
    """
    Renders the main page with the music playlist.
    """
    playlist = list(collection.find({"validated": True}).sort("created_at", 1))
    return render(request, 'index.html', {"playlist": playlist})


def add_music(request):
    """
    Handles adding a new music title via POST request.
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            return JsonResponse({"error": "Title is required"}, status=400)

        # Search YouTube
        yt = search_youtube(title)
        if not yt:
            return JsonResponse({"error": "Music not found on YouTube"}, status=404)

        # Parse YouTube title into song_name and artist
        video_title = yt["title"]
        if '-' in video_title:
            song_name, artist = map(str.strip, video_title.split('-', 1))
        else:
            song_name = video_title
            artist = "Unknown"

        # Prepare data
        data = {
            "song_name": song_name,
            "artist": artist,
            "youtube_video_id": yt["video_id"],
            "youtube_url": f"https://www.youtube.com/watch?v={yt['video_id']}",
            "thumbnail": yt["thumbnail"],
            "validated": True,
            "created_at": datetime.utcnow()
        }

        # Insert into MongoDB
        collection.insert_one(data)
        return JsonResponse({"message": "Music added", "data": data})

    return JsonResponse({"error": "Invalid request method"}, status=405)


def get_playlist(request):
    """
    Returns the current playlist as JSON.
    """
    playlist = list(collection.find({"validated": True}, {"_id": 0}).sort("created_at", 1))
    return JsonResponse({"playlist": playlist})


def delete_music(request):
    """
    Deletes a music track after playback.
    Expects JSON with 'youtube_video_id'.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            video_id = data.get("youtube_video_id")
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not video_id:
            return JsonResponse({"error": "Video ID is required"}, status=400)

        result = collection.delete_one({"youtube_video_id": video_id})
        if result.deleted_count == 0:
            return JsonResponse({"error": "Music not found"}, status=404)

        return JsonResponse({"message": "Music deleted"})

    return JsonResponse({"error": "Invalid request method"}, status=405)
