from flask import Flask, request, jsonify, send_file
import os
import logging
from utils.downloader import download_youtube_video, get_youtube_formats, get_youtube_info
from utils.helpers import validate_url, sanitize_filename

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/youtube/info', methods=['GET'])
def youtube_info():
    """Get YouTube video information without cookies"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    if not validate_url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    try:
        info = get_youtube_info(url)
        if info:
            return jsonify({
                'success': True,
                'info': {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description')[:200] + '...' if info.get('description') else ''
                }
            })
        else:
            return jsonify({'error': 'Could not fetch video information'}), 500
    except Exception as e:
        logger.error(f"Error getting YouTube info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/formats', methods=['GET'])
def youtube_formats():
    """Get available formats for YouTube video without cookies"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    if not validate_url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    try:
        formats = get_youtube_formats(url)
        if formats:
            return jsonify({
                'success': True,
                'formats': formats
            })
        else:
            return jsonify({'error': 'Could not fetch available formats'}), 500
    except Exception as e:
        logger.error(f"Error getting YouTube formats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/download', methods=['POST'])
def youtube_download():
    """Download YouTube video without cookies"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    url = data.get('url')
    format_type = data.get('format', 'best')
    download_path = data.get('download_path', 'downloads')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not validate_url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    try:
        file_path = download_youtube_video(url, download_path, format_type)
        if file_path:
            filename = os.path.basename(file_path)
            return jsonify({
                'success': True,
                'message': 'Download completed successfully',
                'file_path': file_path,
                'filename': filename
            })
        else:
            return jsonify({'error': 'Download failed'}), 500
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/youtube/download/file', methods=['GET'])
def download_file():
    """Download the actual file"""
    file_path = request.args.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        filename = os.path.basename(file_path)
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Other routes remain unchanged...
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
