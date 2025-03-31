from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from models.schemas import Channel, ChannelCreate, Video
from database.db import get_db
from services.youtube_service import YouTubeService
from services.repository import (
    get_channels, get_channel, create_channel, get_videos, 
    update_videos_for_channel, get_paginated_videos  # Add this import
)

router = APIRouter()
youtube_service = YouTubeService()

@router.get("/channels", response_model=List[Channel])
def read_channels(db: Session = Depends(get_db)):
    channels = get_channels(db)
    return channels

@router.post("/channels/add", response_model=Channel)
async def add_channel(channel_data: ChannelCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if channel already exists
    db_channel = get_channel(db, channel_data.id)
    if db_channel:
        return db_channel
    
    # Get channel info from YouTube
    channel_info = youtube_service.get_channel_info(channel_data.id)
    if not channel_info:
        raise HTTPException(status_code=404, detail="Channel not found on YouTube")
    
    # Add section from request
    channel_info["section"] = channel_data.section
    
    # Create channel in database
    db_channel = create_channel(db, channel_info)
    
    # Fetch videos in background
    background_tasks.add_task(
        fetch_and_update_videos, 
        channel_id=db_channel.id, 
        uploads_playlist_id=db_channel.uploads_playlist_id
    )
    
    return db_channel

@router.get("/videos", response_model=List[Video])
def read_videos(section: Optional[str] = None, db: Session = Depends(get_db)):
    videos_data = get_videos(db, section)
    
    # Format response
    result = []
    for video, channel_title, section in videos_data:
        video_dict = {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "published_at": video.published_at,
            "thumbnail_url": video.thumbnail_url,
            "channel_title": channel_title,
            "section": section
        }
        result.append(video_dict)
    
    return result

@router.get("/videos/load-more")
def load_more_videos(section: Optional[str] = None, cursor: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Load more videos with pagination
    - section: Filter by section (optional)
    - cursor: Last video ID (optional)
    """
    # Default to 10 videos per page
    limit = 10
    
    try:
        # Get videos with pagination
        videos_data = get_paginated_videos(db, section, cursor, limit)
        
        # Format response
        result = []
        for video, channel_title, section in videos_data["videos"]:
            video_dict = {
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "published_at": video.published_at,
                "thumbnail_url": video.thumbnail_url,
                "channel_title": channel_title,
                "section": section
            }
            result.append(video_dict)
        
        # Return videos and next cursor for pagination
        return {
            "videos": result,
            "nextCursor": videos_data["next_cursor"]
        }
    except Exception as e:
        print(f"Error loading more videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/channels/{channel_id}/refresh")
async def refresh_channel(channel_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_channel = get_channel(db, channel_id)
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Refresh videos in background
    background_tasks.add_task(
        fetch_and_update_videos, 
        channel_id=db_channel.id, 
        uploads_playlist_id=db_channel.uploads_playlist_id
    )
    
    return {"status": "Refresh task started"}

# Background task to fetch and update videos
async def fetch_and_update_videos(channel_id: str, uploads_playlist_id: str):
    """Fetch and update videos for a channel"""
    # Get a new DB session (since we're in a background task)
    db = next(get_db())
    
    # Fetch initial batch of videos from YouTube
    max_results = 50  # Increased from 10 to 50
    videos, next_page_token = youtube_service.get_playlist_videos(uploads_playlist_id, max_results)
    
    # Update database with initial batch
    update_videos_for_channel(db, channel_id, videos)
    
    # If there are more videos, fetch next pages
    while next_page_token:
        # Fetch next page of videos
        videos, next_page_token = youtube_service.get_playlist_videos(
            uploads_playlist_id, 
            max_results, 
            next_page_token
        )
        
        # Update database with next batch
        update_videos_for_channel(db, channel_id, videos)
        
        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print(f"Finished updating videos for channel {channel_id}")
    