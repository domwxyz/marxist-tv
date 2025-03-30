import React from 'react';

const VideoList = ({ videos, currentVideo, onSelectVideo }) => {
  return (
    <div className="video-list">
      <h3>Latest Videos</h3>
      <div className="video-scroll">
        {videos.length === 0 ? (
          <p>No videos found</p>
        ) : (
          videos.map((video) => (
            <div
              key={video.id}
              className={`video-item ${
                currentVideo && video.id === currentVideo.id ? 'active' : ''
              }`}
              onClick={() => onSelectVideo(video)}
            >
              <div className="thumbnail">
                <img src={video.thumbnail_url} alt={video.title} />
              </div>
              <div className="video-info">
                <h4>{video.title}</h4>
                <p>{video.channel_title}</p>
                <p className="date">
                  {new Date(video.published_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default VideoList;
