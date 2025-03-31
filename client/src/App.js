import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayer from './components/VideoPlayer';
import VideoList from './components/VideoList';
import SectionSelector from './components/SectionSelector';
import { fetchVideos } from './services/youtube';

function App() {
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [sections, setSections] = useState(['all']);
  const [currentSection, setCurrentSection] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch videos when component mounts or section changes
  useEffect(() => {
    const getVideos = async () => {
      try {
        setLoading(true);
        const data = await fetchVideos(currentSection);
        setVideos(data);
        
        // Set the first video as current if none is selected
        if (!currentVideo && data.length > 0) {
          setCurrentVideo(data[0]);
        }
        
        // Extract unique sections from the videos
        const uniqueSections = ['all', ...new Set(data.map(video => video.section))];
        setSections(uniqueSections);
        
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch videos:', err);
        setError('Failed to load videos. Please try again later.');
        setLoading(false);
      }
    };

    getVideos();
    
    // Set up periodic refreshing (every 5 minutes)
    const intervalId = setInterval(getVideos, 300000);
    return () => clearInterval(intervalId);
  }, [currentSection]);

  const handleVideoSelect = (video) => {
    setCurrentVideo(video);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSectionChange = (section) => {
    setCurrentSection(section);
    setCurrentVideo(null);
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
        <h1>Revolutionary Communist TV</h1>
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
        />
      </main>
    </div>
  );
}

export default App;
