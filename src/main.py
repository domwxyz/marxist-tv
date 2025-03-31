import json
import os
from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from database.db import engine, Base
from routes.api import router as api_router
from services.background import start_periodic_update

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="YouTube Aggregator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Background task for periodic updates
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_periodic_update())

# Load channels from config file
@app.on_event("startup")
async def load_channels_from_config():
    try:
        from database.db import get_db
        from services.youtube_service import YouTubeService
        from services.repository import get_channel, create_channel
        
        # Create a YouTube service instance
        youtube_service = YouTubeService()
        
        # Get DB session
        db = next(get_db())
        
        # Check if channels.json exists
        config_path = os.path.join(os.path.dirname(__file__), "..", "channels.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                channels = json.load(f)
            
            print(f"Loading {len(channels)} channels from configuration file...")
            
            # Add each channel
            for channel_data in channels:
                # Skip if channel already exists
                existing = get_channel(db, channel_data.get("channel_id", channel_data.get("id")))
                if existing:
                    print(f"Channel {channel_data.get('channel_id', channel_data.get('id'))} already exists")
                    continue
                
                # Get channel info from YouTube
                channel_id = channel_data.get("channel_id", channel_data.get("id"))
                if not channel_id:
                    print("Missing channel_id in config")
                    continue
                    
                channel_info = youtube_service.get_channel_info(channel_id)
                if not channel_info:
                    print(f"Could not find channel {channel_id}")
                    continue
                
                # Add section from config
                channel_info["section"] = channel_data["section"]
                
                # Create channel in database
                db_channel = create_channel(db, channel_info)
                print(f"Added channel: {db_channel.title}")
                
                # Fetch videos (in the background)
                asyncio.create_task(
                    fetch_and_update_videos(
                        channel_id=db_channel.id,
                        uploads_playlist_id=db_channel.uploads_playlist_id
                    )
                )
    except Exception as e:
        print(f"Error loading channels from config: {e}")

async def fetch_and_update_videos(channel_id: str, uploads_playlist_id: str):
    # Import here to avoid circular imports
    from database.db import get_db
    from services.youtube_service import YouTubeService
    from services.repository import update_videos_for_channel
    
    youtube_service = YouTubeService()
    db = next(get_db())
    
    # Fetch videos from YouTube
    videos = youtube_service.get_playlist_videos(uploads_playlist_id)
    
    # Update database
    update_videos_for_channel(db, channel_id, videos)
    
    print(f"Updated {len(videos)} videos for channel {channel_id}")

@app.get("/")
def read_root():
    return {"status": "API is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    