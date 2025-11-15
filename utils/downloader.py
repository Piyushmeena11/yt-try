import os
import logging
from typing import Optional
from .youtube_dl import youtube_downloader

logger = logging.getLogger(__name__)

def download_youtube_video(url: str, download_path: str = "downloads", 
                          format_type: str = "best") -> Optional[str]:
    """
    Download YouTube video without cookies
    """
    try:
        # Validate YouTube URL
        if 'youtube.com' not in url and 'youtu.be' not in url:
            raise ValueError("Invalid YouTube URL")
        
        # Get video info first
        video_info = youtube_downloader.get_video_info(url)
        if not video_info:
            raise Exception("Could not fetch video information")
        
        logger.info(f"Downloading: {video_info['title']}")
        
        # Download the video
        file_path = youtube_downloader.download_video(url, download_path, format_type)
        
        if file_path and os.path.exists(file_path):
            logger.info(f"Successfully downloaded: {file_path}")
            return file_path
        else:
            raise Exception("Download failed - file not found")
            
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        raise

def get_youtube_formats(url: str) -> Optional[list]:
    """
    Get available formats for YouTube video
    """
    try:
        return youtube_downloader.get_available_formats(url)
    except Exception as e:
        logger.error(f"Error getting YouTube formats: {str(e)}")
        return None

def get_youtube_info(url: str) -> Optional[dict]:
    """
    Get YouTube video information
    """
    try:
        return youtube_downloader.get_video_info(url)
    except Exception as e:
        logger.error(f"Error getting YouTube info: {str(e)}")
        return None
