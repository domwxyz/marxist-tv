import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// API configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  // State management (no Redux needed!)
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [sections, setSections] = useState(['all']);
  const [currentSection, setCurrentSection] = useState('all');
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [stats, setStats] = useState(null);
  
  const LIMIT = 20; // Videos per page

  // Fetch sections on mount
  useEffect(() => {
    fetch(`${API_URL}/api/sections`)
      .then(res => res.json())
      .then(data => setSections(data.sections))
      .catch(err => console.error('Failed to fetch sections:', err));
    
    // Also fetch stats
    fetch(`${API_URL}/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Failed to fetch stats:', err));
  }, []);

  // Fetch videos
  const fetchVideos = useCallback(async (section, newOffset = 0, append = false) => {
    setLoading(true);
    
    try {
      const response = await fetch(
        `${API_URL}/api/videos?section=${section}&offset=${newOffset}&limit=${LIMIT}`
      );
      const data = await response.json();
      
      if (append) {
        setVideos(prev => [...prev, ...data.videos]);
      } else {
        setVideos(data.videos);
        // Set first video as current when loading new section
        if (data.videos.length > 0) {
          setCurrentVideo(data.videos[0]);
        }
      }
      
      setHasMore(data.has_more);
      setOffset(newOffset);
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load videos when section changes
  useEffect(() => {
    setOffset(0);
    setCurrentVideo(null);
    fetchVideos(currentSection, 0, false);
  }, [currentSection, fetchVideos]);

  // Handle section change
  const handleSectionChange = (section) => {
    setCurrentSection(section);
  };

  // Handle video selection
  const handleVideoSelect = (video) => {
    setCurrentVideo(video);
    // Smooth scroll to top on mobile
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Load more videos
  const handleLoadMore = () => {
    if (!loading && hasMore) {
      const newOffset = offset + LIMIT;
      fetchVideos(currentSection, newOffset, true);
    }
  };

  // Format date helper
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Loading state
  if (loading && videos.length === 0) {
    return (
      <div className="app-container">
        <Header sections={sections} currentSection={currentSection} onSectionChange={handleSectionChange} />
        <div className="loading">Loading videos...</div>
        <Footer stats={stats} />
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header 
        sections={sections} 
        currentSection={currentSection} 
        onSectionChange={handleSectionChange} 
      />
      
      <div className="content-container">
        {/* Video Player Column */}
        <div className="main-column">
          <div className="card-container player-container">
            {currentVideo ? (
              <VideoPlayer video={currentVideo} formatDate={formatDate} />
            ) : (
              <div className="video-placeholder">Select a video to watch</div>
            )}
          </div>
        </div>
        
        {/* Video List Column */}
        <div className="list-container card-container">
          <VideoList 
            videos={videos}
            currentVideo={currentVideo}
            onSelectVideo={handleVideoSelect}
            onLoadMore={handleLoadMore}
            hasMore={hasMore}
            isLoading={loading}
            formatDate={formatDate}
          />
        </div>
      </div>
      
      <Footer stats={stats} />
    </div>
  );
}

// Header Component
function Header({ sections, currentSection, onSectionChange }) {
  return (
    <header>
      <div className="header-content">
        <img src="/images/logo.png" alt="Logo" className="logo" />
        <h1>Marxist TV</h1>
      </div>
      <div className="section-selector">
        {sections.map(section => (
          <button
            key={section}
            className={currentSection === section ? 'active' : ''}
            onClick={() => onSectionChange(section)}
          >
            {section === 'all' ? 'All Sections' : section}
          </button>
        ))}
      </div>
    </header>
  );
}

// Video Player Component
function VideoPlayer({ video, formatDate }) {
  return (
    <div className="video-player">
      <div className="video-container">
        <iframe
          src={`https://www.youtube.com/embed/${video.id}`}
          title={video.title}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
      <div className="video-info">
        <h2>{video.title}</h2>
        <p className="channel-title">{video.channel_title}</p>
        <p className="publish-date">{formatDate(video.published_at)}</p>
        <p className="video-description">{video.description}</p>
      </div>
    </div>
  );
}

// Video List Component
function VideoList({ videos, currentVideo, onSelectVideo, onLoadMore, hasMore, isLoading, formatDate }) {
  return (
    <div className="video-list">
      <h3>Latest Videos</h3>
      <div className="video-scroll">
        {videos.map(video => (
          <div
            key={video.id}
            className={`video-item ${currentVideo?.id === video.id ? 'active' : ''}`}
            onClick={() => onSelectVideo(video)}
          >
            <div className="thumbnail">
              <img src={video.thumbnail_url} alt={video.title} />
            </div>
            <div className="video-info">
              <h4>{video.title}</h4>
              <p>{video.channel_title}</p>
              <p className="date">{formatDate(video.published_at)}</p>
            </div>
          </div>
        ))}
      </div>
      
      {hasMore && (
        <div className="load-more-container">
          <button 
            className="load-more-button" 
            onClick={onLoadMore}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </div>
  );
}

// Footer Component
function Footer({ stats }) {
  return (
    <footer>
      <a href="https://communistusa.org">Revolutionary Communists of America</a>
      {stats && (
        <span> 
          • {stats.video_count} videos from {stats.channel_count} channels
          {stats.oldest_video && stats.oldest_video !== "N/A" && (
            <span> • Archive since {new Date(stats.oldest_video).getFullYear()}</span>
          )}
        </span>
      )}
    </footer>
  );
}

export default App;
