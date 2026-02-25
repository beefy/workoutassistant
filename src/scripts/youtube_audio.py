#!/usr/bin/env python3
"""
YouTube Audio Downloader Script
This script searches for a video title + "Music Video" and downloads the audio.
"""

import os
import sys
import yt_dlp
from pathlib import Path

def search_and_download_music_video(title: str, download_path: str = "downloads") -> str:
    """
    Search for a video with the given title + "Music Video" and download its audio.
    
    Args:
        title (str): The song/video title to search for
        download_path (str): Directory to save the downloaded audio
    
    Returns:
        str: Path to the downloaded audio file
    """
    try:
        # Create download directory if it doesn't exist
        Path(download_path).mkdir(exist_ok=True)
        
        # Search for the video using YouTube search
        search_query = f"{title} Music Video"
        print(f"Searching for: {search_query}")
        
        # Configure yt-dlp options for searching and downloading audio
        ydl_search_opts = {
            'quiet': True,
            'no_warnings': True
        }
        
        # Create a search URL (YouTube search results)
        search_url = f"ytsearch1:{search_query}"
        
        # First, extract video info to get the actual video URL and title
        with yt_dlp.YoutubeDL(ydl_search_opts) as ydl:
            search_results = ydl.extract_info(search_url, download=False)
            
        if not search_results or 'entries' not in search_results or not search_results['entries']:
            raise Exception(f"No results found for '{search_query}'")
        
        video_info = search_results['entries'][0]
        video_url = video_info['webpage_url']
        video_title = video_info['title']
        
        print(f"Found video: {video_title}")
        print(f"Video URL: {video_url}")
        
        # Configure yt-dlp options for downloading audio
        ydl_download_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False
        }
        
        print(f"Downloading audio: {video_title}")
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
            ydl.download([video_url])
        
        # Find the downloaded file (it will have .mp3 extension after processing)
        # Clean the title for filename matching
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Look for the downloaded file
        download_dir = Path(download_path)
        mp3_files = list(download_dir.glob("*.mp3"))
        
        if mp3_files:
            # Get the most recently created mp3 file
            output_file = max(mp3_files, key=os.path.getctime)
            print(f"Downloaded successfully: {output_file}")
            return str(output_file)
        else:
            # Fallback: look for any audio file
            audio_files = list(download_dir.glob("*"))
            audio_files = [f for f in audio_files if f.is_file() and not f.name.startswith('.')]
            if audio_files:
                output_file = max(audio_files, key=os.path.getctime)
                print(f"Downloaded successfully: {output_file}")
                return str(output_file)
            else:
                raise Exception("Downloaded file not found")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """
    Main function to run the script with command line arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python youtube_audio.py <song_title> [download_directory]")
        print("Example: python youtube_audio.py \"Bohemian Rhapsody\" \"my_music\"")
        sys.exit(1)
    
    title = sys.argv[1]
    download_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads"
    
    result = search_and_download_music_video(title, download_dir)
    
    if result:
        print(f"\nSuccess! Audio downloaded to: {result}")
    else:
        print("\nFailed to download audio.")
        sys.exit(1)

if __name__ == "__main__":
    main()