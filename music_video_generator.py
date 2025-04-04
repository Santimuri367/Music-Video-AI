#!/usr/bin/env python3
"""
AI-Powered Music Video Story Generator (simplified version without MoviePy)

This script generates lyrics and music based on a theme, and prepares for video generation
1. Using Claude to create lyrics based on a theme
2. Using Suno to generate music from those lyrics
3. Using OpenAI's DALL-E to create images for each line of lyrics
"""
import os
import sys
import json
import time
import argparse
import requests
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
from PIL import Image
from io import BytesIO

# Create a simple helper class to update progress in the background
class ProgressUpdater:
    def __init__(self, job_dict, key):
        self.job_dict = job_dict
        self.key = key
    
    def update(self, value, status=None):
        if self.job_dict and self.key in self.job_dict:
            self.job_dict[self.key]['progress'] = value
            if status:
                self.job_dict[self.key]['status'] = status

# Load environment variables
load_dotenv()

# API keys - HARDCODED FOR DIRECT USE
SUNO_API_KEY = os.getenv("SUNO_API_KEY")  # Hardcoded API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API endpoints
SUNO_API_BASE_URL = "https://apibox.erweima.ai/api/v1"

class LyricsGenerator:
    """Class to generate lyrics using Anthropic's Claude model."""
    
    def __init__(self):
        """Initialize the Anthropic client."""
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def truncate_title(self, title, max_length=80):
        """
        Truncate a title to a maximum length, preserving whole words.
        
        Args:
            title: Original title string
            max_length: Maximum allowed length
            
        Returns:
            Truncated title
        """
        if len(title) <= max_length:
            return title
        
        # Remove any quotation marks first
        title = title.strip('"\'')
        
        # Split into words and start truncating
        words = title.split()
        truncated = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                truncated.append(word)
                current_length += len(word) + 1
            else:
                break
        
        # If no words could be added, slice the title
        result = ' '.join(truncated).strip() or title[:max_length]
        
        # Optionally re-add quotes if needed
        return result
    
    def generate_lyrics(self, prompt, style=None, num_verses=2, has_chorus=True):
        """
        Generate lyrics using Anthropic's Claude model.
        
        Args:
            prompt: The main theme or idea for the lyrics
            style: Music style (e.g., "rock", "pop", "rap")
            num_verses: Number of verses to generate
            has_chorus: Whether to include a chorus
            
        Returns:
            dict: Generated lyrics with title and content
        """
        # Construct a detailed prompt for Claude
        system_prompt = """You are a professional songwriter with expertise in many musical styles.
        Create original, creative, and emotionally resonant lyrics that feel authentic to the requested style.
        Structure the lyrics properly and ensure they have a cohesive theme."""
        
        style_instruction = f"Write in {style} style. " if style else ""
        structure_instruction = f"Include {num_verses} verses"
        structure_instruction += " and a chorus that repeats." if has_chorus else "."
        
        user_prompt = f"{style_instruction}Write lyrics for a song about: {prompt}. {structure_instruction} \
        Include a title at the top. Format the output so verses and chorus are clearly separated."
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract lyrics and title
        lyrics_text = response.content[0].text
        
        # Parse out the title (assuming it's the first line)
        lines = lyrics_text.strip().split('\n')
        title = lines[0].replace("#", "").strip()
        
        # Truncate the title to max 80 characters
        title = self.truncate_title(title)
        
        content = '\n'.join(lines[1:]).strip()
        
        return {
            "title": title,
            "content": content,
            "full_text": lyrics_text
        }


class MusicGenerator:
    """Class to generate music using Suno API with lyrics."""
    
    def __init__(self, debug=False):
        """
        Initialize with the Suno API key.
        
        Args:
            debug: Enable detailed logging
        """
        self.api_key = SUNO_API_KEY  # Using the hardcoded API key
        self.debug = debug
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Verify API key is set
        if not self.api_key or self.api_key.strip() == "":
            print("ERROR: SUNO_API_KEY environment variable is not set or is empty.")
            print("Please add your Suno API key to the .env file.")
    
    def generate_music(self, title, lyrics, style, custom_mode=True, instrumental=False, model="V3_5"):
        """
        Generate music with lyrics using Suno API.
        
        Args:
            title: Song title
            lyrics: Lyrics content
            style: Music style description
            custom_mode: Whether to use custom mode (True) or non-custom mode (False)
            instrumental: Whether to generate instrumental music (no lyrics)
            model: Model version to use (V3_5 or V4)
            
        Returns:
            dict: Response from Suno API containing task ID and other details
        """
        # Prepare request payload
        payload = {
            "prompt": lyrics,
            "style": style if custom_mode else "",
            "title": title if custom_mode else "",
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": "https://example.com/callback"  # Placeholder, won't be used
        }
        
        # Log request for debugging
        print(f"Sending request to Suno API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {SUNO_API_BASE_URL}/generate")
        
        # Make API request to generate audio
        try:
            response = requests.post(
                f"{SUNO_API_BASE_URL}/generate",
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout to prevent hanging
            )
            
            # Check for successful response
            if response.status_code == 200:
                resp_json = response.json()
                if self.debug:
                    print(f"API Response: {json.dumps(resp_json, indent=2)}")
                return resp_json
            else:
                print(f"Error generating music: Status code {response.status_code}")
                print(f"Response: {response.text}")
                
                # Try to parse as JSON to provide better error info
                try:
                    error_data = response.json()
                    if 'code' in error_data and 'msg' in error_data:
                        print(f"API Error Code: {error_data['code']}")
                        print(f"Error Message: {error_data['msg']}")
                        
                        if error_data['code'] == 401:
                            print("Authentication failed. Please check your API key.")
                        elif error_data['code'] == 429:
                            print("Insufficient credits. Please add credits to your account.")
                        elif error_data['code'] == 413:
                            print("Theme or prompt too long. Please use a shorter theme or lyrics.")
                except:
                    pass  # Ignore if not JSON
                
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error when contacting Suno API: {e}")
            return None
    
    def check_generation_status(self, task_id):
        """
        Check the status of a generation task.
        
        Args:
            task_id: The task ID returned from generate_music
            
        Returns:
            dict: Task details including status and results if available
        """
        # List of potential endpoints to check
        endpoints = [
            f"{SUNO_API_BASE_URL}/generate/record-info?taskId={task_id}",
            f"{SUNO_API_BASE_URL}/generate/status?taskId={task_id}",
            f"{SUNO_API_BASE_URL}/generate/result?taskId={task_id}",
            f"{SUNO_API_BASE_URL}/task/{task_id}",
            f"{SUNO_API_BASE_URL}/generate/{task_id}"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"Checking status at: {endpoint}")
                response = requests.get(endpoint, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    print("Status check successful")
                    return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error checking endpoint {endpoint}: {e}")
        
        print("All endpoints failed for status check")
        return None
    
    def download_music(self, audio_url, output_path, max_retries=5):
        """
        Download the generated music to a local file with retry mechanism.
        
        Args:
            audio_url: URL to the generated audio
            output_path: Path where to save the downloaded file
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"Download attempt {retry_count + 1}/{max_retries} from {audio_url}")
                
                # Try with streaming (better for large files)
                with requests.get(audio_url, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    
                    # Get file size if available
                    file_size = int(response.headers.get('content-length', 0))
                    if file_size:
                        print(f"File size: {file_size / 1024 / 1024:.2f} MB")
                    
                    # Download with progress tracking
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if file_size:
                                    progress = (downloaded / file_size) * 100
                                    print(f"\rProgress: {progress:.1f}%", end='')
                    print("\nDownload complete!")
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"File saved to {output_path}")
                        return True
                    else:
                        print("Downloaded file is empty. Retrying...")
                
            except Exception as e:
                print(f"Download error: {e}")
            
            # Increase wait time between retries
            wait_time = 2 ** retry_count
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
        
        return False
    
    def monitor_and_download(self, task_id, output_path, max_checks=15, check_interval=15):
        """
        Monitor a task until completion and download the result.
        
        Args:
            task_id: Task ID to monitor
            output_path: Where to save the downloaded file
            max_checks: Maximum number of status checks
            check_interval: Seconds between checks
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Monitoring task ID: {task_id}")
        print(f"Will save to: {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save task ID to a file for later use if needed
        with open('last_task_id.txt', 'w') as f:
            f.write(task_id)
        print(f"Task ID saved to last_task_id.txt")
        
        # Track how long we've been waiting
        total_wait_time = 0
        max_total_wait_time = 300  # 5 minutes total timeout
        
        checks = 0
        while checks < max_checks:
            print(f"\nCheck {checks + 1}/{max_checks} (Total wait: {total_wait_time} seconds)...")
            
            try:
                task_details = self.check_generation_status(task_id)
                
                if not task_details:
                    print("Could not retrieve task details, waiting before retry...")
                    time.sleep(check_interval)
                    total_wait_time += check_interval
                    checks += 1
                    continue
                
                # Print full response for debugging
                print("Full API Response:")
                print(json.dumps(task_details, indent=2))
                
                # Extract status with multiple fallback methods
                def extract_status(details):
                    status_paths = [
                        ['data', 'status'],
                        ['status'],
                        ['data', 'data', 'status']
                    ]
                    
                    for path in status_paths:
                        current = details
                        try:
                            for key in path:
                                current = current[key]
                            return current
                        except (KeyError, TypeError):
                            continue
                    
                    return None
                
                status = extract_status(task_details)
                
                print(f"Current status: {status}")
                
                # Define final and failure statuses
                final_statuses = [
                    'SUCCESS', 'FIRST_SUCCESS', 
                    'complete', 'finished', 'success',
                    'FINAL_SUCCESS'
                ]
                failure_statuses = [
                    'CREATE_TASK_FAILED', 'GENERATE_AUDIO_FAILED', 
                    'CALLBACK_EXCEPTION', 'SENSITIVE_WORD_ERROR', 
                    'failed', 'error', 'FAILED'
                ]
                
                # Progress-like statuses that we'll continue waiting for
                progress_statuses = [
                    'PENDING', 'TEXT_SUCCESS', 
                    'GENERATING', 'IN_PROGRESS'
                ]
                
                if status in final_statuses:
                    print("Task is complete!")
                    
                    # Find audio URL with multiple fallback methods
                    def find_audio_url(obj):
                        # First, try to find direct audio URLs from the flat structure
                        if isinstance(obj, dict):
                            # Check for direct URL keys
                            for key in ['audioUrl', 'sourceAudioUrl']:
                                if key in obj and isinstance(obj[key], str) and obj[key].startswith('http'):
                                    # Prioritize .mp3 URLs
                                    if '.mp3' in obj[key]:
                                        return obj[key]
                            
                            # Second pass for other audio URL types if no mp3 found
                            for key in ['audioUrl', 'sourceAudioUrl', 'streamAudioUrl', 'sourceStreamAudioUrl']:
                                if key in obj and isinstance(obj[key], str) and obj[key].startswith('http'):
                                    return obj[key]
                        
                        # If not found, try nested paths
                        url_paths = [
                            ['data', 'response', 'sunoData', 0, 'audioUrl'],
                            ['data', 'response', 'sunoData', 0, 'sourceAudioUrl'],
                            ['data', 'audioUrl'],
                            ['data', 'sunoData', 0, 'audioUrl'],
                            ['sunoData', 0, 'audioUrl'],
                            ['results', 0, 'audioUrl']
                        ]
                        
                        for path in url_paths:
                            current = obj
                            try:
                                for key in path:
                                    current = current[key]
                                
                                # Validate URL
                                if current and isinstance(current, str) and current.startswith('http'):
                                    return current
                            except (KeyError, TypeError, IndexError):
                                continue
                        
                        # If still not found, recursively search in nested objects
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if k.lower() in ['audiourl', 'sourceaudiourl'] and isinstance(v, str) and v.startswith('http'):
                                    return v
                                
                                if isinstance(v, (dict, list)):
                                    result = find_audio_url(v)
                                    if result:
                                        return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_audio_url(item)
                                if result:
                                    return result
                                    
                        return None
                    
                    audio_url = find_audio_url(task_details)
                    
                    if audio_url:
                        print(f"Found audio URL: {audio_url}")
                        success = self.download_music(audio_url, output_path)
                        return success
                    else:
                        print("No valid audio URL found in the response.")
                        
                        # Additional debugging: print all URLs found
                        def print_all_urls(obj):
                            urls = []
                            def extract_urls(item):
                                if isinstance(item, dict):
                                    for k, v in item.items():
                                        if isinstance(v, str) and v.startswith('http'):
                                            urls.append((k, v))
                                        elif isinstance(v, (dict, list)):
                                            extract_urls(v)
                                elif isinstance(item, list):
                                    for elem in item:
                                        extract_urls(elem)
                            
                            extract_urls(obj)
                            return urls
                        
                        found_urls = print_all_urls(task_details)
                        print("All URLs found in the response:")
                        for key, url in found_urls:
                            print(f"{key}: {url}")
                        
                        return False
                    
                elif status in failure_statuses:
                    print(f"Task failed with status: {status}")
                    return False
                
                elif status in progress_statuses:
                    # If we've been waiting too long, consider it a failure
                    if total_wait_time >= max_total_wait_time:
                        print(f"Exceeded maximum wait time ({max_total_wait_time} seconds). Aborting.")
                        return False
                    
                    print(f"Task still processing. Waiting {check_interval} seconds...")
                    time.sleep(check_interval)
                    total_wait_time += check_interval
                
                else:
                    print(f"Unexpected status: {status}. Continuing to wait...")
                    time.sleep(check_interval)
                    total_wait_time += check_interval
                
                checks += 1
            
            except Exception as e:
                print(f"Unexpected error during monitoring: {e}")
                print("Waiting before retry...")
                time.sleep(check_interval)
                total_wait_time += check_interval
                checks += 1
        
        print("Exceeded maximum checks. Task may still be processing.")
        print(f"You can check again later using the task ID: {task_id}")
        return False


class ImageGenerator:
    """Class to generate images using OpenAI's DALL-E model."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_image(self, prompt, output_path, size="1024x1024"):
        """
        Generate an image using DALL-E based on a prompt.
        
        Args:
            prompt: Text description for the image
            output_path: Where to save the image
            size: Image size (1024x1024, 512x512, or 256x256)
            
        Returns:
            str: Path to the saved image
        """
        print(f"Generating image for: {prompt}")
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=f"Create a cinematic scene for a music video with the following lyrics: '{prompt}'. Make it visually striking with artistic lighting and composition. No text in the image.",
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            print(f"Image generated: {image_url}")
            
            # Download the image
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img.save(output_path)
            print(f"Image saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def generate_images_for_lyrics(self, lyrics, output_dir="images"):
        """
        Generate images for each verse/section of the lyrics.
        
        Args:
            lyrics: Full lyrics text
            output_dir: Directory to save generated images
            
        Returns:
            list: Paths to the generated images
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Split lyrics into meaningful sections
        # This is a simple split by empty lines, but could be more sophisticated
        sections = [section.strip() for section in lyrics.split("\n\n") if section.strip()]
        
        image_paths = []
        for i, section in enumerate(sections):
            # Clean up the section - keep it concise for better image generation
            # Take just the first few lines to avoid overloading the prompt
            lines = section.split('\n')
            if len(lines) > 4:
                image_prompt = "\n".join(lines[:4])
            else:
                image_prompt = section
                
            output_path = os.path.join(output_dir, f"image_{i:02d}.png")
            path = self.generate_image(image_prompt, output_path)
            
            if path:
                image_paths.append(path)
                # Sleep to avoid rate limits
                time.sleep(2)
            
        return image_paths


def generate_music_video(theme, style="pop", verses=2, has_chorus=True, output_dir="output", progress_updater=None):
    """
    Generate lyrics, music, and images for a music video from a theme.
    
    Args:
        theme: The main theme or idea for the song
        style: Music style (e.g., "rock", "pop", "rap")
        verses: Number of verses
        has_chorus: Whether to include a chorus
        output_dir: Directory to save all generated files
        progress_updater: Optional ProgressUpdater instance to track progress
        
    Returns:
        str: Path to the audio file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Generate lyrics
    if progress_updater:
        progress_updater.update(10, "Generating lyrics...")
    print(f"Generating lyrics about '{theme}' in {style} style...")
    lyrics_gen = LyricsGenerator()
    lyrics_result = lyrics_gen.generate_lyrics(
        theme, 
        style=style,
        num_verses=verses,
        has_chorus=has_chorus
    )
    
    lyrics_title = lyrics_result['title']
    lyrics_content = lyrics_result['content']
    
    print(f"\nGenerated title: {lyrics_title}")
    print("Generated lyrics:")
    print("-" * 40)
    print(lyrics_content)
    print("-" * 40)
    
    # Save lyrics to file
    lyrics_path = os.path.join(output_dir, "lyrics.txt")
    with open(lyrics_path, 'w') as f:
        f.write(f"{lyrics_title}\n\n{lyrics_content}")
    print(f"Lyrics saved to {lyrics_path}")
    
    # Step 2: Generate music
    if progress_updater:
        progress_updater.update(20, "Generating music...")
    print("\nGenerating music...")
    music_gen = MusicGenerator(debug=True)
    audio_path = os.path.join(output_dir, "song.mp3")
    
    generation_response = music_gen.generate_music(
        lyrics_title,
        lyrics_content,
        style,
        custom_mode=True,
        instrumental=False,
        model="V3_5"
    )
    
    if not generation_response:
        print("Failed to start music generation. Please check the error messages above.")
        return None
    
    # Extract task ID from response
    task_id = None
    try:
        task_id = generation_response.get('data', {}).get('taskId')
        if not task_id:
            # Try alternative paths
            task_id = generation_response.get('taskId')
            
            if not task_id:
                # Search recursively
                def find_task_id(obj):
                    if isinstance(obj, dict):
                        if 'taskId' in obj:
                            return obj['taskId']
                        for k, v in obj.items():
                            result = find_task_id(v)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_task_id(item)
                            if result:
                                return result
                    return None
                
                task_id = find_task_id(generation_response)
    except Exception as e:
        print(f"Error extracting task ID: {e}")
        return None
    
    if not task_id:
        print("No task ID returned from Suno API.")
        return None
    
    print(f"Music generation started with task ID: {task_id}")
    
    # Monitor and download the generated music
    success = music_gen.monitor_and_download(task_id, audio_path)
    if not success:
        print("Failed to generate and download music.")
        return None
    
    # Step 3: Generate images for each section of lyrics
    if progress_updater:
        progress_updater.update(50, "Generating images...")
    print("\nGenerating images for lyrics...")
    image_gen = ImageGenerator()
    image_dir = os.path.join(output_dir, "images")
    image_paths = image_gen.generate_images_for_lyrics(lyrics_content, image_dir)
    
    if not image_paths:
        print("Failed to generate images.")
        return None
    
    # Note: We skip the video generation step in this simplified version
    
    # For now, just mark as complete and return the audio path
    if progress_updater:
        progress_updater.update(100, "Complete")
    
    # Return the audio path since we're not generating video
    return audio_path


def main():
    """Main function to orchestrate music and image generation."""
    parser = argparse.ArgumentParser(description='Generate AI music and images')
    parser.add_argument('--theme', type=str, required=True, help='Theme or idea for the song')
    parser.add_argument('--style', type=str, default='pop', help='Music style (e.g., rock, pop, rap)')
    parser.add_argument('--verses', type=int, default=2, help='Number of verses')
    parser.add_argument('--chorus', action='store_true', help='Include a chorus')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    
    args = parser.parse_args()
    
    # Check for API keys first - OpenAI and Anthropic still from .env
    if not SUNO_API_KEY:
        print("ERROR: SUNO_API_KEY is not set.")
        return
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please add your Anthropic API key to the .env file.")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please add your OpenAI API key to the .env file.")
        return
    
    # Generate music and images
    generate_music_video(
        args.theme,
        style=args.style,
        verses=args.verses,
        has_chorus=args.chorus,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()











