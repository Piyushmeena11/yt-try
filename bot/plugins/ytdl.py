import os
import re
import yt_dlp
import asyncio
import logging
from datetime import datetime
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils.human_size import human_readable_size
from bot.utils.progress import progress_for_pyrogram
from bot import app, OWNER_ID, LOGGER

# Configure yt-dlp to work without cookies
def get_ydl_opts(quality, download_path):
    """Get yt-dlp options without cookies"""
    return {
        'format': quality,
        'outtmpl': os.path.join(download_path, '%(title).100s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'no_warnings': False,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': True,
        'no_color': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        # Cookie avoidance settings
        'cookiefile': None,
        'cookiesfrombrowser': None,
        'usenetrc': False,
        'mark_watched': False,
        'simulate': False,
        'skip_download': False,
    }

def get_video_info(url):
    """Extract video information without using cookies"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        'cookiefile': None,
        'cookiesfrombrowser': None,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        LOGGER.error(f"Error getting video info: {str(e)}")
        return None

def get_available_formats(info):
    """Get available formats for the video"""
    formats = []
    
    if 'formats' in info:
        for f in info['formats']:
            if f.get('filesize') or f.get('filesize_approx'):
                format_note = f.get('format_note', 'N/A')
                ext = f.get('ext', 'N/A')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                
                if f.get('height'):
                    # Video format
                    format_id = f'{f["height"]}p'
                    if f.get('fps'):
                        format_id += f'{f["fps"]}'
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        format_type = 'video+audio'
                    elif f.get('vcodec') != 'none':
                        format_type = 'video'
                    else:
                        format_type = 'audio'
                    
                    formats.append({
                        'format_id': f['format_id'],
                        'display_name': f'{format_id} ({format_type}) - {ext} - {human_readable_size(filesize)}',
                        'filesize': filesize,
                        'type': 'video'
                    })
                elif f.get('acodec') != 'none':
                    # Audio format
                    abr = f.get('abr', 0)
                    formats.append({
                        'format_id': f['format_id'],
                        'display_name': f'audio ({abr}kbps) - {ext} - {human_readable_size(filesize)}',
                        'filesize': filesize,
                        'type': 'audio'
                    })
    
    # Remove duplicates and sort
    seen = set()
    unique_formats = []
    for f in formats:
        if f['display_name'] not in seen:
            seen.add(f['display_name'])
            unique_formats.append(f)
    
    # Sort by filesize descending for videos, keep audio separate
    video_formats = [f for f in unique_formats if f['type'] == 'video']
    audio_formats = [f for f in unique_formats if f['type'] == 'audio']
    
    video_formats.sort(key=lambda x: x['filesize'], reverse=True)
    audio_formats.sort(key=lambda x: x['filesize'], reverse=True)
    
    return video_formats + audio_formats

@app.on_message(filters.command("ytdl") & filters.user(OWNER_ID))
async def youtube_dl_handler(client, message):
    """Handle YouTube download commands"""
    if len(message.command) < 2:
        await message.reply_text("Please provide a YouTube URL.\nUsage: /ytdl <url>")
        return

    url = message.command[1]
    
    # Validate YouTube URL
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    if not re.match(youtube_regex, url):
        await message.reply_text("Please provide a valid YouTube URL.")
        return

    processing_msg = await message.reply_text("🔍 **Fetching video information...**")

    try:
        # Get video information without cookies
        info = get_video_info(url)
        if not info:
            await processing_msg.edit_text("❌ Failed to fetch video information. The video might be private or unavailable.")
            return

        title = info.get('title', 'Unknown Title')
        duration = info.get('duration', 0)
        uploader = info.get('uploader', 'Unknown Uploader')
        
        # Create format selection buttons
        formats = get_available_formats(info)
        if not formats:
            await processing_msg.edit_text("❌ No downloadable formats found.")
            return

        # Create keyboard with format options
        keyboard = []
        row = []
        
        for i, fmt in enumerate(formats[:20]):  # Limit to 20 formats to avoid too many buttons
            callback_data = f"ytdl_{message.id}_{fmt['format_id']}"
            row.append(InlineKeyboardButton(
                fmt['display_name'][:20] + "...", 
                callback_data=callback_data
            ))
            if len(row) == 2:  # 2 buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"ytdl_cancel_{message.id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Prepare video info text
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
        info_text = f"**📹 Title:** {title}\n"
        info_text += f"**👤 Uploader:** {uploader}\n"
        info_text += f"**⏱ Duration:** {duration_str}\n"
        info_text += f"**📊 Available Formats:** {len(formats)}\n\n"
        info_text += "**Select a format to download:**"
        
        await processing_msg.edit_text(info_text, reply_markup=reply_markup)
        
    except Exception as e:
        LOGGER.error(f"Error in YouTube DL handler: {str(e)}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

@app.on_callback_query(filters.regex(r"^ytdl_"))
async def youtube_dl_callback(client, callback_query):
    """Handle YouTube download format selection"""
    data = callback_query.data
    message_id = callback_query.message.reply_to_message.id if callback_query.message.reply_to_message else callback_query.message.id
    
    if data.startswith(f"ytdl_cancel_{message_id}"):
        await callback_query.message.edit_text("❌ Download cancelled.")
        await callback_query.answer()
        return
    
    # Extract format ID from callback data
    parts = data.split('_')
    if len(parts) < 3:
        await callback_query.answer("Invalid selection", show_alert=True)
        return
    
    format_id = parts[2]
    url = callback_query.message.reply_to_message.command[1] if callback_query.message.reply_to_message else None
    
    if not url:
        await callback_query.answer("URL not found", show_alert=True)
        return
    
    await callback_query.answer("Starting download...")
    
    # Update message to show download starting
    await callback_query.message.edit_text("⬇️ **Starting download...**\n\nThis may take a while depending on the video size and format.")
    
    try:
        # Create download directory
        download_path = f"downloads/{callback_query.from_user.id}"
        os.makedirs(download_path, exist_ok=True)
        
        # Download with selected format without cookies
        ydl_opts = get_ydl_opts(format_id, download_path)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    # You can add progress tracking here if needed
                    pass
            
            ydl.params['progress_hooks'] = [progress_hook]
            info = ydl.extract_info(url, download=True)
        
        # Find the downloaded file
        downloaded_file = ydl.prepare_filename(info)
        
        if os.path.exists(downloaded_file):
            # Get file size
            file_size = os.path.getsize(downloaded_file)
            
            # Send the file
            await callback_query.message.edit_text("📤 **Uploading to Telegram...**")
            
            caption = f"**{info.get('title', 'Video')}**\n\n"
            caption += f"💾 Size: {human_readable_size(file_size)}\n"
            caption += f"🎬 Format: {format_id}\n"
            caption += f"👤 Requested by: {callback_query.from_user.mention}"
            
            # Determine whether it's video or audio
            if downloaded_file.endswith(('.mp4', '.mkv', '.webm', '.flv')):
                await client.send_video(
                    chat_id=callback_query.message.chat.id,
                    video=downloaded_file,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        "**📤 Uploading...**",
                        callback_query.message,
                        datetime.now()
                    )
                )
            else:
                await client.send_audio(
                    chat_id=callback_query.message.chat.id,
                    audio=downloaded_file,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        "**📤 Uploading...**",
                        callback_query.message,
                        datetime.now()
                    )
                )
            
            # Clean up downloaded file
            os.remove(downloaded_file)
            
            await callback_query.message.edit_text("✅ **Download completed successfully!**")
            
        else:
            await callback_query.message.edit_text("❌ Downloaded file not found.")
            
    except Exception as e:
        LOGGER.error(f"Error downloading YouTube video: {str(e)}")
        await callback_query.message.edit_text(f"❌ Download failed: {str(e)}")
    
    finally:
        # Clean up download directory if empty
        try:
            download_dir = f"downloads/{callback_query.from_user.id}"
            if os.path.exists(download_dir) and not os.listdir(download_dir):
                os.rmdir(download_dir)
        except:
            pass

@app.on_message(filters.command("ytdl_format") & filters.user(OWNER_ID))
async def youtube_dl_format_helper(client, message):
    """Helper command to show available formats"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /ytdl_format <url>")
        return
    
    url = message.command[1]
    processing_msg = await message.reply_text("🔍 Fetching available formats...")
    
    try:
        info = get_video_info(url)
        if not info:
            await processing_msg.edit_text("❌ Failed to fetch video information.")
            return
        
        formats = get_available_formats(info)
        if not formats:
            await processing_msg.edit_text("❌ No formats available.")
            return
        
        response = f"**Available formats for:** {info.get('title', 'Unknown')}\n\n"
        
        for i, fmt in enumerate(formats[:15]):  # Limit to 15 formats
            response += f"{i+1}. {fmt['display_name']}\n"
            response += f"   Format ID: `{fmt['format_id']}`\n\n"
        
        if len(formats) > 15:
            response += f"... and {len(formats) - 15} more formats\n"
        
        response += "\nUse `/ytdl <url>` to download with interactive format selection."
        
        await processing_msg.edit_text(response)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
