# AI-Powered Music Video Story Generator

This project automatically generates complete music videos with AI-created lyrics, soundtrack, and visuals based on a user's input theme.

## Features

- **AI-Generated Lyrics**: Uses Claude (Anthropic) to create song lyrics based on a theme.
- **AI-Generated Music**: Uses Suno AI to convert the lyrics into a full song.
- **AI-Generated Visuals**: Uses DALL-E to create images for each section of the lyrics.
- **Automatic Video Assembly**: Combines the soundtrack and visuals into a complete music video.
- **Web Interface**: Provides an easy-to-use web app to create and view generated videos.

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ai-music-video-generator
```

2. Create a `.env` file in the project directory with your API keys:
```
SUNO_API_KEY=your_suno_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

You can generate a music video directly from the command line:

```bash
python music_video_generator.py --theme "A journey through space and time" --style "rock" --verses 2 --chorus
```

Command line arguments:
- `--theme`: The main theme or idea for your song (required)
- `--style`: Music style (e.g., rock, pop, rap) (default: pop)
- `--verses`: Number of verses (default: 2)
- `--chorus`: Include this flag to add a chorus (default: True)
- `--output-dir`: Output directory (default: output)

### Web Application

For a more user-friendly experience, you can run the web application:

```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000`. The web interface allows you to:

1. Enter a theme or story idea for your music video
2. Select a music style
3. Specify the number of verses and whether to include a chorus
4. Monitor the generation process
5. View and download the completed music video

## How It Works

1. **Lyrics Generation**: The system sends your theme to Claude to create lyrics in the specified style.
2. **Music Generation**: The lyrics are sent to Suno AI, which composes and produces a song based on them.
3. **Image Generation**: Each section of the lyrics is sent to DALL-E to create matching visual scenes.
4. **Video Assembly**: Using MoviePy, the system combines the images with the audio to create a complete music video.

## Project Structure

- `music_video_generator.py`: Core functionality for generating music videos
- `app.py`: Flask web application
- `templates/`: HTML templates for the web interface
- `main.py`: Original lyrics and music generator (from the reference project)
- `check_status.py`: Utility to check Suno API task status
- `download_song.py`: Utility to download generated songs

## Notes

- The generation process can take several minutes to complete.
- Suno API may have usage limits. Check their documentation for details.
- Image generation requires OpenAI credits.

## Presentation Slides

For a class presentation, you might want to cover:

1. **Project Overview**: What problem does this solve? What does it create?
2. **Demo**: Show a sample music video created with the tool.
3. **Technical Architecture**: Explain how the different AI services work together.
4. **Challenges Faced**: Discuss any issues you encountered and how you solved them.
5. **Future Improvements**: What features could be added with more time/resources?

## Credits

- Lyrics generation: Claude by Anthropic
- Music generation: Suno AI
- Image generation: DALL-E by OpenAI
- Based on the original project by [kaw393939](https://github.com/kaw393939/suno-lyrics-music-generator)