# Marxist TV

A web application for aggregating video content from multiple YouTube channels in one location. This project consists of a FastAPI backend that fetches and stores YouTube video data, and a React frontend for viewing the videos.

## Project Overview

Marxist TV is designed to gather content from specified YouTube channels and present them in a unified interface. It's ideal for organizations that want to create a curated video hub from multiple sources.

### Features

- Aggregates videos from multiple YouTube channels
- Organizes content by sections (RCA, RCI, RCP)
- Automatically updates video content periodically
- Responsive web interface for viewing videos
- Filter videos by section

## Project Structure

```
marxist-tv/
├── client/               # React frontend
│   ├── public/           # Static files
│   └── src/              # React source code
│       ├── components/   # React components
│       └── services/     # API service functions
├── src/                  # FastAPI backend
│   ├── database/         # Database configuration
│   ├── models/           # Data models
│   ├── routes/           # API endpoints
│   └── services/         # Business logic
└── channels.json         # Channel configuration
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- YouTube Data API key

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/marxist-tv.git
   cd marxist-tv
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp src/.env.example src/.env
   ```
   
4. Edit the `.env` file and add your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   DATABASE_URL=sqlite:///videos.db
   ```

### Frontend Setup

1. Navigate to the client directory:
   ```
   cd client
   ```

2. Install dependencies:
   ```
   npm install
   ```

## Running the Application

### Start the Backend

```
cd src
uvicorn main:app --reload
```

The API will be available at http://localhost:8000. API documentation is available at http://localhost:8000/docs.

### Start the Frontend

In a new terminal:

```
cd client
npm start
```

The web application will open automatically at http://localhost:3000.

## Configuration

### Adding YouTube Channels

Edit the `channels.json` file to add new channels:

```json
[
  {
    "channel_id": "YOUTUBE_CHANNEL_ID",
    "section": "SECTION_NAME"
  }
]
```

- `channel_id`: The YouTube channel ID
- `section`: A category for organizing content (e.g., "RCA", "RCI", "RCP")

The application will automatically load channels from this file on startup.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the LICENSE file for details.
