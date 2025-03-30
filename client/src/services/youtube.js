import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fetchVideos = async (section = 'all') => {
  try {
    const response = await axios.get(`${API_URL}/videos`, {
      params: { section }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching videos:', error);
    throw error;
  }
};

export const fetchChannels = async () => {
  try {
    const response = await axios.get(`${API_URL}/channels`);
    return response.data;
  } catch (error) {
    console.error('Error fetching channels:', error);
    throw error;
  }
};
