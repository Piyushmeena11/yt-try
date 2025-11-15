import yt_dlp
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'no_cookies': True,
            'cookiefile': None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
            },
            'extract_flat': False,
            'ignoreerrors': True,
            'logtostderr': False,
            'nooverwrites': True,
            'noprogress': True,
        }
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get video information without using cookies
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'formats': info.get('formats', []),
                        'thumbnail': info.get('thumbnail', ''),
                        'description': info.get('description', ''),
                        'webpage_url': info.get('webpage_url', url)
                    }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None
    
    def download_video(self, url: str, download_path: str = "downloads", 
                      format_type: str = "best") -> Optional[str]:
        """
        Download YouTube video without using cookies
        """
        try:
            # Create download directory if it doesn't exist
            os.makedirs(download_path, exist_ok=True)
            
            # Update download options
            download_opts = self.ydl_opts.copy()
            download_opts.update({
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'format': format_type,
            })
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                # Extract info and download
                info = ydl.extract_info(url, download=True)
                if info:
                    filename = ydl.prepare_filename(info)
                    return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None
    
    def get_available_formats(self, url: str) -> Optional[list]:
        """
        Get available formats for the video
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'formats' in info:
                    formats = []
                    for fmt in info['formats']:
                        format_note = fmt.get('format_note', 'unknown')
                        ext = fmt.get('ext', 'unknown')
                        filesize = fmt.get('filesize', fmt.get('filesize_approx', 0))
                        formats.append({
                            'format_id': fmt['format_id'],
                            'ext': ext,
                            'format_note': format_note,
                            'filesize': filesize,
                            'resolution': fmt.get('resolution', 'unknown')
                        })
                    return formats
            return None
        except Exception as e:
            logger.error(f"Error getting formats: {str(e)}")
            return None

# Global instance
youtube_downloader = YouTubeDownloader()
