#!/usr/bin/env python3
"""
Web interface for the AI-Powered Music Video Story Generator
"""
import os
import traceback
import threading
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from music_video_generator import generate_music_video, ProgressUpdater

# Hardcoding the Suno API key directly in app.py
SUNO_API_KEY = os.getenv("SUNO_API_KEY")  # Hardcoded API key

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # For flash messages

# Add a filter to check if a file exists
@app.template_filter('file_exists')
def file_exists(path):
    return os.path.isfile(os.path.join('static', path))

# Create output directory if it doesn't exist
os.makedirs('static/output', exist_ok=True)

# Dictionary to store the status of generation jobs
generation_jobs = {}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', jobs=generation_jobs)

@app.route('/generate', methods=['POST'])
def generate():
    """Handle form submission to generate music."""
    # Get form data
    theme = request.form.get('theme')
    style = request.form.get('style', 'pop')
    verses = int(request.form.get('verses', 2))
    has_chorus = 'chorus' in request.form
    
    if not theme:
        flash('Please enter a theme for your music.')
        return redirect(url_for('index'))
    
    # Create a unique ID for this job
    job_id = f"{theme.replace(' ', '_')}_{style}_{verses}"
    output_dir = os.path.join('static/output', job_id)
    
    # Add job to the dictionary with initial error handling
    generation_jobs[job_id] = {
        'theme': theme,
        'style': style,
        'verses': verses,
        'has_chorus': has_chorus,
        'status': 'Starting...',
        'progress': 0,
        'output_dir': output_dir,
        'audio_path': None,
        'lyrics_path': None,
        'image_paths': [],
        'error_message': None
    }
    
    # Start generation in a separate thread
    thread = threading.Thread(
        target=generate_in_background,
        args=(job_id, theme, style, verses, has_chorus, output_dir)
    )
    thread.start()
    
    flash(f'Your music generation has started! Job ID: {job_id}')
    return redirect(url_for('view_job', job_id=job_id))

def generate_in_background(job_id, theme, style, verses, has_chorus, output_dir):
    """
    Generate music and images in the background and update the job status.
    
    Args:
        job_id: Unique identifier for this job
        theme: Theme or idea for the song
        style: Music style
        verses: Number of verses
        has_chorus: Whether to include a chorus
        output_dir: Output directory for generated files
    """
    try:
        # Create a progress updater for this job
        progress_updater = ProgressUpdater(generation_jobs, job_id)
        
        # Detailed error logging
        generation_jobs[job_id]['error_details'] = []
        
        # Start the generation process
        audio_path = generate_music_video(
            theme,
            style=style,
            verses=verses,
            has_chorus=has_chorus,
            output_dir=output_dir,
            progress_updater=progress_updater
        )
        
        if audio_path:
            # Update job status on success
            job = generation_jobs[job_id]
            job['status'] = 'Complete'
            job['progress'] = 100
            job['audio_path'] = os.path.relpath(audio_path, 'static')
            
            # Add lyrics path
            lyrics_path = os.path.join(output_dir, 'lyrics.txt')
            if os.path.exists(lyrics_path):
                job['lyrics_path'] = os.path.relpath(lyrics_path, 'static')
            
            # Add image paths
            image_dir = os.path.join(output_dir, 'images')
            if os.path.exists(image_dir):
                job['image_paths'] = [
                    os.path.relpath(os.path.join(image_dir, img), 'static')
                    for img in os.listdir(image_dir)
                    if img.endswith('.png')
                ]
        else:
            # Update job status on failure
            generation_jobs[job_id]['status'] = 'Failed'
            generation_jobs[job_id]['progress'] = 0
            generation_jobs[job_id]['error_message'] = 'Failed to generate audio. No audio file created.'
            generation_jobs[job_id]['error_details'].append('Audio generation returned None')
    
    except Exception as e:
        # Comprehensive error handling
        import traceback
        
        # Log the full error traceback
        error_trace = traceback.format_exc()
        print(f"Error in generation job {job_id}: {error_trace}")
        
        # Update job status with detailed error information
        generation_jobs[job_id]['status'] = 'Failed'
        generation_jobs[job_id]['progress'] = 0
        generation_jobs[job_id]['error_message'] = str(e)
        generation_jobs[job_id]['error_details'] = [
            f"Type: {type(e).__name__}",
            f"Error: {str(e)}",
            f"Traceback: {error_trace}"
        ]

@app.route('/job/<job_id>')
def view_job(job_id):
    """View the status and result of a specific job."""
    if job_id not in generation_jobs:
        flash('Job not found.')
        return redirect(url_for('index'))
    
    return render_template('job.html', job=generation_jobs[job_id], job_id=job_id)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)