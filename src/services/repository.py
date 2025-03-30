from sqlalchemy.orm import Session
from models.models import Channel, Video
from typing import List, Optional
import datetime

def get_channels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Channel).offset(skip).limit(limit).all()

def get_channel(db: Session, channel_id: str):
    return db.query(Channel).filter(Channel.id == channel_id).first()

def create_channel(db: Session, channel_data: dict):
    db_channel = Channel(
        id=channel_data["id"],
        title=channel_data["title"],
        section=channel_data["section"],
        uploads_playlist_id=channel_data["uploads_playlist_id"]
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def get_videos(db: Session, section: Optional[str] = None, skip: int = 0, limit: int = 20):
    query = db.query(
        Video,
        Channel.title.label("channel_title"),
        Channel.section
    ).join(Channel)
    
    if section and section.lower() != "all":
        query = query.filter(Channel.section == section)
    
    return query.order_by(Video.published_at.desc()).offset(skip).limit(limit).all()

def create_video(db: Session, video_data: dict):
    db_video = Video(
        id=video_data["id"],
        title=video_data["title"],
        description=video_data["description"],
        channel_id=video_data["channel_id"],
        published_at=video_data["published_at"],
        thumbnail_url=video_data["thumbnail_url"]
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def update_videos_for_channel(db: Session, channel_id: str, videos_data: List[dict]):
    # Get existing video IDs for this channel
    existing_video_ids = set([
        video_id for (video_id,) in 
        db.query(Video.id).filter(Video.channel_id == channel_id).all()
    ])
    
    # Process new videos
    new_video_ids = set()
    for video_data in videos_data:
        new_video_ids.add(video_data["id"])
        
        # Check if video already exists
        db_video = db.query(Video).filter(Video.id == video_data["id"]).first()
        
        if db_video:
            # Update existing video
            db_video.title = video_data["title"]
            db_video.description = video_data["description"]
            db_video.published_at = video_data["published_at"]
            db_video.thumbnail_url = video_data["thumbnail_url"]
        else:
            # Create new video
            create_video(db, video_data)
    
    # Optionally: Remove videos that no longer exist in the channel
    # videos_to_delete = existing_video_ids - new_video_ids
    # if videos_to_delete:
    #     db.query(Video).filter(Video.id.in_(videos_to_delete)).delete(synchronize_session=False)
    
    db.commit()
    