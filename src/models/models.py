from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.db import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    section = Column(String, index=True)
    uploads_playlist_id = Column(String)
    
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    channel_id = Column(String, ForeignKey("channels.id"))
    published_at = Column(String, index=True)
    thumbnail_url = Column(String)
    
    channel = relationship("Channel", back_populates="videos")
    