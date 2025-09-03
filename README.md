# Marxist TV

A web application for aggregating video content from multiple YouTube channels in one location. This project consists of a FastAPI backend that fetches and stores YouTube video data, and a React frontend for viewing the videos.

## Project Overview

Marxist TV is designed to gather content from specified YouTube channels and present them in a unified interface. It's ideal for organizations that want to create a curated video hub from multiple sources.

### Features

- Aggregates videos from multiple YouTube channels
- Organizes content by sections (RCA, RCI, RCP)
- Automatically updates video content every 30 minutes
- Responsive web interface for viewing videos
- Filter videos by section

## Project Structure

```
marxist-tv/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── channels.json     # Channel configuration
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
└── frontend/
    ├── src/
    │   ├── App.js       # React application
    │   ├── App.css      # Styles
    │   └── index.js     # Entry point
    └── package.json     # Node dependencies
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- YouTube Data API key

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   
4. Edit the `.env` file and add your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   DATABASE_URL=sqlite:///videos.db
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

## Running the Application

### Start the Backend

```
cd backend
python main.py
```

The API will be available at http://localhost:8000. API documentation is available at http://localhost:8000/docs.

### Start the Frontend

In a new terminal:

```
cd frontend
npm start
```

The web application will open automatically at http://localhost:3000.

## Configuration

### Adding YouTube Channels

Edit the `backend/channels.json` file to add new channels:

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

### Initial Load Settings

By default, the application fetches the complete video history on first run. You can adjust this in `backend/main.py`:

- `FETCH_ALL_ON_INITIAL = True` - Fetch entire channel history (default)
- `UPDATE_INTERVAL = 1800` - Update interval in seconds (default: 30 minutes)

## Production Deployment

For production deployment on a VPS or cloud server:

1. Build the frontend: `npm run build`
2. Set up a reverse proxy with Nginx
3. Run the backend with a process manager like systemd
4. Configure SSL with Let's Encrypt

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the LICENSE file for details.
