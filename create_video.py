#!/usr/bin/env python3
"""
Enhanced Video Generator for AI Music Video Project
Combines audio and images into a complete music video with better error handling and debugging
"""

import os
import sys
import time
import logging
from pathlib import Path
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, TextClip

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger('video_generator')

def create_slideshow_video(audio_path, image_folder, output_path, duration_per_image=None, 
                          fade_duration=1.0, add_lyrics=False, lyrics_path=None):
    """
    Create a slideshow video from images and audio with enhanced features.
    
    Args:
        audio_path: Path to the audio file
        image_folder: Path to the folder containing images
        output_path: Path to save the output video
        duration_per_image: How long each image should be shown (in seconds), or None to calculate from audio
        fade_duration: Duration of the fade transition between images (in seconds)
        add_lyrics: Whether to add lyrics as subtitles
        lyrics_path: Path to the lyrics file
        
    Returns:
        str: Path to the output video
    """
    try:
        logger.info(f"Starting video creation from {image_folder} with audio {audio_path}")
        logger.info(f"Will save to {output_path}")
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get audio clip and its duration
        logger.info("Loading audio file...")
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        logger.info(f"Audio duration: {audio_duration:.2f} seconds")
        
        # Get list of images in the folder
        image_files = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        
        if not image_files:
            logger.error(f"No images found in {image_folder}")
            return None
        
        logger.info(f"Found {len(image_files)} images")
        
        # Calculate actual duration per image based on audio length
        if duration_per_image is None:
            actual_duration = audio_duration / len(image_files)
        else:
            actual_duration = duration_per_image
            
        logger.info(f"Each image will be shown for {actual_duration:.2f} seconds")
        
        # Create image clips
        clips = []
        
        for i, img_path in enumerate(image_files):
            try:
                logger.info(f"Processing image {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
                
                # Create the clip
                clip = ImageClip(img_path, duration=actual_duration)
                
                # Set position to center
                clip = clip.set_position('center')
                
                # Add the clip to our list
                clips.append(clip)
                
            except Exception as e:
                logger.error(f"Error processing image {img_path}: {e}")
                # Continue with other images rather than failing
        
        if not clips:
            logger.error("No valid image clips were created")
            return None
        
        # Concatenate clips
        logger.info("Concatenating video clips...")
        video = concatenate_videoclips(clips, method="compose")
        
        # Add lyrics as subtitles if requested
        if add_lyrics and lyrics_path and os.path.exists(lyrics_path):
            try:
                logger.info(f"Adding lyrics from {lyrics_path}")
                with open(lyrics_path, 'r') as f:
                    lyrics_text = f.read()
                # TODO: Implement synchronized lyrics (requires parsing timestamps)
                # This is a simple implementation that displays the title at the beginning
                lyrics_lines = lyrics_text.split('\n')
                if len(lyrics_lines) > 0:
                    title = lyrics_lines[0]
                    title_clip = TextClip(title, fontsize=30, color='white', bg_color='rgba(0,0,0,0.5)',
                                         font='Arial-Bold', size=video.size)
                    title_clip = title_clip.set_position('bottom').set_duration(5)
                    video = CompositeVideoClip([video, title_clip])
            except Exception as e:
                logger.error(f"Error adding lyrics: {e}")
        
        # Set the audio
        logger.info("Adding audio to video...")
        final_video = video.set_audio(audio_clip)
        
        # Ensure the video size is consistent and suitable for most displays
        final_video = final_video.resize(width=1280, height=720)
        
        # Write the result to a file
        logger.info(f"Writing video to {output_path}...")
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            preset='faster',  # Use faster preset for quicker encoding
            threads=4,        # Use multiple threads
            logger=None       # Disable moviepy's verbose logging
        )
        
        # Clean up
        audio_clip.close()
        
        # Verify the output file exists and has size > 0
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully created video: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
            return output_path
        else:
            logger.error(f"Output file {output_path} was not created or is empty")
            return None
            
    except Exception as e:
        logger.error(f"Error in create_slideshow_video: {e}", exc_info=True)
        return None

def main():
    """Command line interface for video creation with better error handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a music video from images and audio')
    parser.add_argument('--audio', type=str, required=True, help='Path to the audio file')
    parser.add_argument('--images', type=str, required=True, help='Path to the folder containing images')
    parser.add_argument('--output', type=str, required=True, help='Path to save the output video')
    parser.add_argument('--duration', type=float, default=None, help='Duration per image (in seconds), or None to calculate from audio')
    parser.add_argument('--fade', type=float, default=1.0, help='Fade duration between images (in seconds)')
    parser.add_argument('--lyrics', type=str, help='Path to lyrics file for adding subtitles')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate paths
    if not os.path.exists(args.audio):
        logger.error(f"Audio file not found: {args.audio}")
        return 1
        
    if not os.path.exists(args.images):
        logger.error(f"Images folder not found: {args.images}")
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Create the video
    start_time = time.time()
    result = create_slideshow_video(
        args.audio, 
        args.images, 
        args.output,
        duration_per_image=args.duration,
        fade_duration=args.fade,
        add_lyrics=bool(args.lyrics),
        lyrics_path=args.lyrics
    )
    
    elapsed_time = time.time() - start_time
    
    if result:
        logger.info(f"Video created successfully in {elapsed_time:.2f} seconds")
        return 0
    else:
        logger.error(f"Failed to create video after {elapsed_time:.2f} seconds")
        return 1

if __name__ == "__main__":
    sys.exit(main())