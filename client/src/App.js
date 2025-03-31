import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayer from './components/VideoPlayer';
import VideoList from './components/VideoList';
import SectionSelector from './components/SectionSelector';
import { fetchVideos, loadMoreVideos } from './services/youtube';

function App() {
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [sections, setSections] = useState(['all']);
  const [currentSection, setCurrentSection] = useState('all');
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [nextCursor, setNextCursor] = useState(null);

  // Fetch videos when component mounts or section changes
  useEffect(() => {
    const getVideos = async () => {
      try {
        setLoading(true);
        setHasMore(true); // Reset pagination when section changes
        setNextCursor(null);
        
        const data = await fetchVideos(currentSection);
        setVideos(data);
        
        // Set the first video as current if none is selected
        if (!currentVideo && data.length > 0) {
          setCurrentVideo(data[0]);
        }
        
        // Extract unique sections from the videos
        if (sections.length <= 1) {
          // Only run this once to initially populate the sections
          const uniqueSections = ['all', ...new Set(data.map(video => video.section))];
          setSections(uniqueSections);
        }
        
        setLoading(false);
        
        // Determine if there might be more videos to load
        setHasMore(data.length >= 10); // Assuming the initial fetch is limited to 10
        setNextCursor(data.length > 0 ? data[data.length - 1].id : null);
      } catch (err) {
        console.error('Failed to fetch videos:', err);
        setError('Failed to load videos. Please try again later.');
        setLoading(false);
        setHasMore(false);
      }
    };

    getVideos();
    
    // Set up periodic refreshing (every 5 minutes) for the initial videos only
    const intervalId = setInterval(() => getVideos(), 300000);
    return () => clearInterval(intervalId);
  }, [currentSection]);

  const handleVideoSelect = (video) => {
    setCurrentVideo(video);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSectionChange = (section) => {
    setCurrentSection(section);
    setCurrentVideo(null);
    setVideos([]);
  };

  const handleLoadMore = async () => {
    if (loadingMore || !hasMore || !nextCursor) return;
    
    try {
      setLoadingMore(true);
      
      const result = await loadMoreVideos(currentSection, nextCursor);
      
      if (result.videos && result.videos.length > 0) {
        // Append new videos to the existing list
        setVideos(prevVideos => [...prevVideos, ...result.videos]);
        
        // Update cursor for next pagination
        setNextCursor(result.nextCursor);
        
        // Determine if there are more videos to load
        setHasMore(!!result.nextCursor);
      } else {
        // No more videos to load
        setHasMore(false);
      }
      
      setLoadingMore(false);
    } catch (err) {
      console.error('Failed to load more videos:', err);
      setError('Failed to load more videos. Please try again later.');
      setLoadingMore(false);
    }
  };

  if (loading && videos.length === 0) {
    return <div className="loading">Loading videos...</div>;
  }

  if (error && videos.length === 0) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="app-container">
      <header>
        <h1>Marxist TV</h1>
        <SectionSelector 
          sections={sections}
          currentSection={currentSection}
          onSectionChange={handleSectionChange}
        />
      </header>

      <main>
        <VideoPlayer video={currentVideo} />
        <VideoList 
          videos={videos}
          currentVideo={currentVideo}
          onSelectVideo={handleVideoSelect}
          onLoadMore={handleLoadMore}
          hasMore={hasMore}
          isLoading={loadingMore}
        />
      </main>
    </div>
  );
}

export default App;
