import React, { useState, useEffect, useRef } from 'react';
import songsData from './songs.json';
import './Music.css';

function Music() {
  const [songs, setSongs] = useState([]);
  const [currentSong, setCurrentSong] = useState(null);
  const [currentCategory, setCurrentCategory] = useState('all');
  const [categories, setCategories] = useState(['all']);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  // Load songs on mount
  useEffect(() => {
    setSongs(songsData.songs);
    setCategories(['all', ...songsData.categories]);
    if (songsData.songs.length > 0) {
      setCurrentSong(songsData.songs[0]);
    }
  }, []);

  // Filter songs by category
  const filteredSongs = currentCategory === 'all' 
    ? songs 
    : songs.filter(song => song.category === currentCategory);

  // Handle song selection
  const handleSongSelect = (song) => {
    setCurrentSong(song);
    setIsPlaying(false);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.load();
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle category change
  const handleCategoryChange = (category) => {
    setCurrentCategory(category);
  };

  // Handle play/pause
  const togglePlayPause = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  // Audio ended handler
  const handleAudioEnd = () => {
    setIsPlaying(false);
  };

  // Format lyrics for display
  const formatLyrics = (lyrics) => {
    if (!lyrics || !lyrics.verses) return null;

    return lyrics.verses.map((section, index) => (
      <div key={index} className="lyrics-section">
        {section.type === 'verse' && (
          <h4 className="verse-header">Verse {section.number}</h4>
        )}
        {section.type === 'chorus' && (
          <h4 className="verse-header">Chorus</h4>
        )}
        {section.type === 'bridge' && (
          <h4 className="verse-header">Bridge</h4>
        )}
        <div className="verse-lines">
          {section.lines.map((line, lineIndex) => (
            <p key={lineIndex} className="lyric-line">{line}</p>
          ))}
        </div>
      </div>
    ));
  };

  return (
    <div className="music-container">
      <div className="content-container">
        {/* Music Player Column */}
        <div className="main-column">
          <div className="card-container player-container">
            {currentSong ? (
              <div className="music-player">
                <div className="audio-controls">
                  <h2>{currentSong.title}</h2>
                  <p className="song-subtitle">{currentSong.subtitle}</p>
                  
                  <div className="audio-player-wrapper">
                    <audio
                      ref={audioRef}
                      src={currentSong.audioFile}
                      onEnded={handleAudioEnd}
                      controls
                      className="audio-element"
                    />
                    <button 
                      className="play-pause-button"
                      onClick={togglePlayPause}
                    >
                      {isPlaying ? '⏸ Pause' : '▶ Play'}
                    </button>
                  </div>
                  
                  <div className="song-metadata">
                    {currentSong.composer && (
                      <p><strong>Composer:</strong> {currentSong.composer}</p>
                    )}
                    {currentSong.lyricist && (
                      <p><strong>Lyricist:</strong> {currentSong.lyricist}</p>
                    )}
                    {currentSong.year && (
                      <p><strong>Year:</strong> {currentSong.year}</p>
                    )}
                  </div>
                </div>

                <div className="lyrics-container">
                  <h3>Lyrics</h3>
                  <div className="lyrics-scroll">
                    {currentSong.description && (
                      <p className="song-description">{currentSong.description}</p>
                    )}
                    {formatLyrics(currentSong.lyrics)}
                    {currentSong.lyrics?.notes && (
                      <div className="lyrics-notes">
                        <p><em>{currentSong.lyrics.notes}</em></p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="video-placeholder">Select a song to view lyrics</div>
            )}
          </div>
        </div>
        
        {/* Song List Column */}
        <div className="list-container card-container">
          <div className="song-list">
            <h3>Revolutionary Songs</h3>
            <div className="category-selector">
              {categories.map(category => (
                <button
                  key={category}
                  className={`category-button ${currentCategory === category ? 'active' : ''}`}
                  onClick={() => handleCategoryChange(category)}
                >
                  {category === 'all' ? 'All Songs' : category}
                </button>
              ))}
            </div>
            <div className="song-scroll">
              {filteredSongs.map(song => (
                <div
                  key={song.id}
                  className={`song-item ${currentSong?.id === song.id ? 'active' : ''}`}
                  onClick={() => handleSongSelect(song)}
                >
                  <div className="song-icon">♪</div>
                  <div className="song-info">
                    <h4>{song.title}</h4>
                    <p className="song-subtitle-list">{song.subtitle}</p>
                    {song.year && <p className="song-year">{song.year}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Music;
