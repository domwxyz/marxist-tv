import React from 'react';

const VideoPlayer = ({ video }) => {
  if (!video) {
    return <div className="video-placeholder">No video selected</div>;
  }

  return (
    <div className="video-player">
      <div className="video-container">
        <iframe
          width="100%"
          height="100%"
          src={`https://www.youtube.com/embed/${video.id}`}
          title={video.title}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      </div>
      <div className="video-info">
        <h2>{video.title}</h2>
        <p className="channel-title">{video.channel_title}</p>
        <p className="publish-date">
          {new Date(video.published_at).toLocaleDateString()}
        </p>
        <p className="video-description">{video.description}</p>
      </div>
    </div>
  );
};

export default VideoPlayer;
