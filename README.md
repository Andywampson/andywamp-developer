# AI Video Generator

Simple local video generator using:
- OpenAI for prompt enhancement
- edge-tts for speech synthesis
- ffmpeg for video rendering

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

OpenAI script enhancement is optional. Set `OPENAI_API_KEY` in your terminal to enable it; without a key, the original prompt is used as narration.

## Web App

```powershell
$env:OPENAI_API_KEY = "your_key_here"
.\.venv\Scripts\python.exe -m streamlit run web.py
```

Add up to five JPG, PNG, or WebP photos as video scenes. The local renderer applies a slow pan and zoom; uploaded photos are not sent to OpenAI or ad services. Without photos, the app uses a plain background.

If Edge TTS is unavailable, the video is still created with a fallback tone instead of speech, and the app displays a warning.

## Command Line

```powershell
.\.venv\Scripts\python.exe App.py --prompt "A cinematic drone shot over a futuristic city at sunrise"
```

Use `--image path\to\photo.jpg` to add a scene. Repeat `--image` for up to five scenes.

## Files
- `web.py` - Streamlit interface
- `App.py` - video generation pipeline
- `output/` - generated videos and audio
