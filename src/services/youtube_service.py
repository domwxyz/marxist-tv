from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeService:
    def __init__(self):
        api_service_name = "youtube"
        api_version = "v3"
        api_key = os.getenv("YOUTUBE_API_KEY")
        
        if not api_key:
            raise ValueError("YouTube API key not found in environment variables")
            
        self.youtube = build(api_service_name, api_version, developerKey=api_key)
    
    def get_channel_info(self, channel_id):
        """Fetch channel information including the uploads playlist ID"""
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails",
                id=channel_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return None
                
            channel_info = response["items"][0]
            return {
                "id": channel_id,
                "title": channel_info["snippet"]["title"],
                "uploads_playlist_id": channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
            }
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return None
    
    def get_playlist_videos(self, playlist_id, max_results=10, page_token=None):
        """Fetch videos from a playlist (typically the uploads playlist)"""
        try:
            request_params = {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": max_results
            }
            
            # Add page token if provided
            if page_token:
                request_params["pageToken"] = page_token
                
            request = self.youtube.playlistItems().list(**request_params)
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]
                
                # Get thumbnail URL safely
                thumbnail_url = ""
                if "thumbnails" in snippet:
                    thumbnails = snippet["thumbnails"]
                    if "high" in thumbnails:
                        thumbnail_url = thumbnails["high"]["url"]
                    elif "default" in thumbnails:
                        thumbnail_url = thumbnails["default"]["url"]
                
                videos.append({
                    "id": video_id,
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail_url": thumbnail_url,
                    "channel_id": snippet["channelId"]
                })
                
            # Return videos list and next page token separately
            return videos, response.get("nextPageToken")
            
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return [], None
            