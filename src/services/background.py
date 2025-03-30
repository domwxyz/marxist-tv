import asyncio
from database.db import get_db
from services.youtube_service import YouTubeService
from services.repository import get_channels, update_videos_for_channel

youtube_service = YouTubeService()

async def start_periodic_update():
    """Start the periodic update task"""
    while True:
        try:
            await update_all_channels()
        except Exception as e:
            print(f"Error in periodic update: {e}")
        
        # Wait for 1 hour before next update
        await asyncio.sleep(3600)

async def update_all_channels():
    """Update all channels in the database"""
    db = next(get_db())
    channels = get_channels(db)
    
    for channel in channels:
        try:
            videos = youtube_service.get_playlist_videos(channel.uploads_playlist_id)
            update_videos_for_channel(db, channel.id, videos)
            print(f"Updated {len(videos)} videos for channel {channel.title}")
        except Exception as e:
            print(f"Error updating channel {channel.id}: {e}")
            continue
        