"""
Marxist TV Backend - Simple YouTube Aggregator
A clean, single-file implementation for aggregating YouTube videos
"""
import os
import json
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///videos.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")
UPDATE_INTERVAL = 1800  # 30 minutes in seconds
FETCH_ALL_ON_INITIAL = True  # Set to True to fetch entire channel history on first run
VIDEOS_PER_CHANNEL_INITIAL = 20  # Only used if FETCH_ALL_ON_INITIAL is False

# Validate API key
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

# YouTube client (module level for reuse)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


# === DATABASE FUNCTIONS ===

async def init_database():
    """Initialize database with tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create videos table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                thumbnail_url TEXT,
                channel_id TEXT NOT NULL,
                channel_title TEXT NOT NULL,
                section TEXT NOT NULL,
                published_at TIMESTAMP NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_published ON videos(published_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_section ON videos(section)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_channel ON videos(channel_id)")
        
        # Create metadata table for tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        await db.commit()
        print("Database initialized")


async def get_videos_from_db(section: str = "all", offset: int = 0, limit: int = 20) -> Dict:
    """Get videos from database with optional filtering"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Build query
        if section == "all":
            query = "SELECT * FROM videos ORDER BY published_at DESC LIMIT ? OFFSET ?"
            params = [limit, offset]
        else:
            query = "SELECT * FROM videos WHERE section = ? ORDER BY published_at DESC LIMIT ? OFFSET ?"
            params = [section, limit, offset]
        
        # Get videos
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            videos = [dict(row) for row in rows]
        
        # Get total count for pagination
        if section == "all":
            count_query = "SELECT COUNT(*) as total FROM videos"
            count_params = []
        else:
            count_query = "SELECT COUNT(*) as total FROM videos WHERE section = ?"
            count_params = [section]
            
        async with db.execute(count_query, count_params) as cursor:
            result = await cursor.fetchone()
            total = dict(result)['total']
        
        return {
            "videos": videos,
            "total": total,
            "has_more": offset + limit < total
        }


async def insert_videos(videos: List[Dict]):
    """Insert or update videos in database"""
    if not videos:
        return
        
    async with aiosqlite.connect(DB_PATH) as db:
        for video in videos:
            await db.execute("""
                INSERT OR REPLACE INTO videos 
                (id, title, description, thumbnail_url, channel_id, channel_title, section, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video['id'],
                video['title'],
                video['description'],
                video['thumbnail_url'],
                video['channel_id'],
                video['channel_title'],
                video['section'],
                video['published_at']
            ))
        
        await db.commit()
        print(f"Inserted/updated {len(videos)} videos")


async def get_latest_video_date(channel_id: str) -> Optional[str]:
    """Get the latest video date we have for a channel"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT MAX(published_at) as latest FROM videos WHERE channel_id = ?",
            [channel_id]
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None


async def update_metadata(key: str, value: str):
    """Update metadata in database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            [key, value]
        )
        await db.commit()


# === YOUTUBE FUNCTIONS ===

def load_channels() -> List[Dict]:
    """Load channels from channels.json"""
    try:
        with open("channels.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("channels.json not found, using empty channel list")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing channels.json: {e}")
        return []


def get_channel_info(channel_id: str) -> Optional[Dict]:
    """Get channel info from YouTube API"""
    try:
        response = youtube.channels().list(
            part="snippet,contentDetails",
            id=channel_id
        ).execute()
        
        if not response.get("items"):
            return None
            
        item = response["items"][0]
        return {
            "id": channel_id,
            "title": item["snippet"]["title"],
            "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"]
        }
    except HttpError as e:
        print(f"YouTube API error getting channel info: {e}")
        return None


def fetch_playlist_videos(playlist_id: str, max_results: int = 50, page_token: str = None) -> tuple:
    """Fetch videos from a YouTube playlist"""
    try:
        request_params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": min(max_results, 50)  # YouTube API max is 50
        }
        
        if page_token:
            request_params["pageToken"] = page_token
            
        response = youtube.playlistItems().list(**request_params).execute()
        
        videos = []
        for item in response.get("items", []):
            # Extract video data
            snippet = item["snippet"]
            
            # Get best available thumbnail
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("high", {}).get("url") or
                thumbnails.get("medium", {}).get("url") or
                thumbnails.get("default", {}).get("url") or
                ""
            )
            
            videos.append({
                "id": item["contentDetails"]["videoId"],
                "title": snippet["title"],
                "description": snippet.get("description", ""),
                "thumbnail_url": thumbnail_url,
                "channel_id": snippet["channelId"],
                "channel_title": snippet["channelTitle"],
                "published_at": snippet["publishedAt"]
            })
        
        return videos, response.get("nextPageToken")
        
    except HttpError as e:
        print(f"YouTube API error fetching videos: {e}")
        return [], None


async def fetch_channel_videos(channel: Dict, since_date: Optional[str] = None, fetch_all: bool = False) -> List[Dict]:
    """
    Fetch videos for a channel
    - since_date: Only fetch videos newer than this date (for incremental updates)
    - fetch_all: Fetch entire channel history (for initial load)
    """
    # Get channel info if we don't have uploads playlist ID
    if "uploads_playlist_id" not in channel:
        info = get_channel_info(channel["channel_id"])
        if not info:
            print(f"Could not get info for channel {channel['channel_id']}")
            return []
        channel["uploads_playlist_id"] = info["uploads_playlist_id"]
        channel["channel_title"] = info["title"]
    
    all_videos = []
    page_token = None
    total_fetched = 0
    
    # Fetch videos page by page
    while True:
        videos, page_token = fetch_playlist_videos(
            channel["uploads_playlist_id"],
            max_results=50,  # Always use max for efficiency
            page_token=page_token
        )
        
        if not videos:
            break
        
        # Add section and channel info to each video
        for video in videos:
            video["section"] = channel["section"]
            if "channel_title" in channel:
                video["channel_title"] = channel["channel_title"]
        
        # If we have a since_date (incremental update), filter videos
        if since_date and not fetch_all:
            # Filter for videos newer than since_date
            new_videos = [v for v in videos if v["published_at"] > since_date]
            all_videos.extend(new_videos)
            
            # If we found a video older than since_date, we can stop
            if any(v["published_at"] <= since_date for v in videos):
                break
        else:
            # Fetch all videos (initial load) or limited number
            all_videos.extend(videos)
            total_fetched += len(videos)
            
            # If not fetching all, limit to VIDEOS_PER_CHANNEL_INITIAL
            if not fetch_all and total_fetched >= VIDEOS_PER_CHANNEL_INITIAL:
                all_videos = all_videos[:VIDEOS_PER_CHANNEL_INITIAL]
                break
        
        # No more pages
        if not page_token:
            break
        
        # Progress indicator for large channels
        if fetch_all and total_fetched % 200 == 0:
            print(f"  ...fetched {total_fetched} videos so far from {channel.get('channel_id')}")
            
        # Small delay to be nice to API
        await asyncio.sleep(0.5)
    
    print(f"Fetched {len(all_videos)} videos from {channel.get('channel_id')}")
    return all_videos


# === UPDATE LOOP ===

async def update_videos_task():
    """Background task that periodically updates videos"""
    while True:
        try:
            print(f"Starting video update at {datetime.now()}")
            await update_metadata("last_update_start", datetime.now().isoformat())
            
            channels = load_channels()
            total_new_videos = 0
            
            for channel in channels:
                # Get the latest video date we have for this channel
                latest_date = await get_latest_video_date(channel["channel_id"])
                
                # Fetch videos (only new ones if we have a latest_date)
                print(f"Checking channel {channel.get('channel_id')} (section: {channel.get('section')})")
                videos = await fetch_channel_videos(channel, since_date=latest_date)
                
                if videos:
                    await insert_videos(videos)
                    total_new_videos += len(videos)
                    print(f"Found {len(videos)} new videos for {channel.get('channel_id')}")
                
                # Small delay between channels to avoid rate limiting
                await asyncio.sleep(1)
            
            await update_metadata("last_update_complete", datetime.now().isoformat())
            await update_metadata("last_update_new_videos", str(total_new_videos))
            
            print(f"Update complete. Found {total_new_videos} new videos. Sleeping for {UPDATE_INTERVAL} seconds.")
            
        except Exception as e:
            print(f"Error in update loop: {e}")
        
        # Wait before next update
        await asyncio.sleep(UPDATE_INTERVAL)


async def initial_load():
    """Load initial videos on first run"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if we have any videos
        async with db.execute("SELECT COUNT(*) FROM videos") as cursor:
            count = await cursor.fetchone()
            if count[0] > 0:
                print(f"Database already has {count[0]} videos, skipping initial load")
                return
    
    print("First run detected, loading initial videos...")
    
    if FETCH_ALL_ON_INITIAL:
        print("FETCH_ALL_ON_INITIAL is True - this will fetch ALL videos from each channel.")
        print("This may take several minutes and use significant API quota on first run...")
    
    channels = load_channels()
    total_videos_loaded = 0
    
    for channel in channels:
        print(f"Loading videos for {channel.get('channel_id')} (section: {channel.get('section')})")
        
        # Fetch all videos if FETCH_ALL_ON_INITIAL is True
        videos = await fetch_channel_videos(channel, fetch_all=FETCH_ALL_ON_INITIAL)
        
        if videos:
            await insert_videos(videos)
            total_videos_loaded += len(videos)
            
        await asyncio.sleep(1)  # Be nice to API
    
    print(f"Initial load complete! Loaded {total_videos_loaded} total videos.")
    await update_metadata("initial_load_complete", datetime.now().isoformat())
    await update_metadata("initial_videos_count", str(total_videos_loaded))


# === FASTAPI APP ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Marxist TV Backend...")
    await init_database()
    await initial_load()
    
    # Start background update task
    asyncio.create_task(update_videos_task())
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Marxist TV API",
    version="2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === API ROUTES ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "name": "Marxist TV API",
        "docs": "/docs"
    }


@app.get("/api/videos")
async def get_videos(
    section: str = Query("all", description="Filter by section or 'all'"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of videos to return")
):
    """Get videos with optional section filter and pagination"""
    result = await get_videos_from_db(section, offset, limit)
    return result


@app.get("/api/sections")
async def get_sections():
    """Get list of available sections"""
    channels = load_channels()
    sections = ["all"] + list(set(c.get("section", "unknown") for c in channels))
    return {"sections": sections}


@app.get("/api/stats")
async def get_stats():
    """Get statistics about the database"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get video count
        async with db.execute("SELECT COUNT(*) as count FROM videos") as cursor:
            video_count = dict(await cursor.fetchone())['count']
        
        # Get channel count
        async with db.execute("SELECT COUNT(DISTINCT channel_id) as count FROM videos") as cursor:
            channel_count = dict(await cursor.fetchone())['count']
        
        # Get date range of videos
        async with db.execute("""
            SELECT 
                MIN(published_at) as oldest,
                MAX(published_at) as newest
            FROM videos
        """) as cursor:
            dates = dict(await cursor.fetchone())
        
        # Get metadata
        metadata = {}
        async with db.execute("SELECT key, value FROM metadata") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                metadata[row[0]] = row[1]
        
        return {
            "video_count": video_count,
            "channel_count": channel_count,
            "oldest_video": dates.get("oldest", "N/A"),
            "newest_video": dates.get("newest", "N/A"),
            "last_update": metadata.get("last_update_complete", "Never"),
            "last_update_new_videos": int(metadata.get("last_update_new_videos", 0)),
            "initial_load_complete": metadata.get("initial_load_complete", "Never"),
            "initial_videos_loaded": int(metadata.get("initial_videos_count", 0))
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
