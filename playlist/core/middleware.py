from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb+srv://jrsalvacion:jrsalvacion@cluster0.lizmpn8.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database("music_db")
page_views = db.get_collection("page_views")

class TrafficMiddleware:
    """Logs each page request into MongoDB"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if 'text/html' in response.get('Content-Type', ''):
            page_views.insert_one({
                "path": request.path,
                "ip": self.get_client_ip(request),
                "user_agent": request.META.get('HTTP_USER_AGENT', ''),
                "timestamp": datetime.utcnow()
            })

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
