#!/usr/bin/env python3
"""
YouTube Audio Downloader Script
This script searches for a video title + "Music Video" and downloads the audio.
"""

import os
import sys
from pytube import Search, YouTube
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
        
        # Search for the video
        search_query = f"{title} Music Video"
        print(f"Searching for: {search_query}")
        
        search = Search(search_query)
        
        if not search.results:
            raise Exception(f"No results found for '{search_query}'")
        
        # Get the first result
        first_video = search.results[0]
        print(f"Found video: {first_video.title}")
        print(f"Video URL: {first_video.watch_url}")
        
        # Create YouTube object
        yt = YouTube(first_video.watch_url)
        
        # Get the audio stream (highest quality available)
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        
        if not audio_stream:
            raise Exception("No audio stream found")
        
        print(f"Downloading audio: {yt.title}")
        print(f"Audio quality: {audio_stream.abr}")
        
        # Download the audio
        output_file = audio_stream.download(output_path=download_path)
        
        # Rename to .mp3 if needed
        if not output_file.endswith('.mp3'):
            base_name = os.path.splitext(output_file)[0]
            mp3_file = f"{base_name}.mp3"
            os.rename(output_file, mp3_file)
            output_file = mp3_file
        
        print(f"Downloaded successfully: {output_file}")
        return output_file
        
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