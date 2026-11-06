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

Optionally upload a separate sponsor image to show as a three-second end card. This is only an image placement; it does not connect to an ad network, serve ads, or track revenue.

If Edge TTS is unavailable, the video is still created with a fallback tone instead of speech, and the app displays a warning.

## Command Line

```powershell
.\.venv\Scripts\python.exe App.py --prompt "A cinematic drone shot over a futuristic city at sunrise"
```

Use `--image path\to\photo.jpg` to add a scene. Repeat `--image` for up to five scenes.
Use `--ad-image path\to\sponsor.jpg` to append a three-second sponsor end card. This is placement only; it does not connect to an ad network or track revenue.

## Files
- `web.py` - Streamlit interface
- `App.py` - video generation pipeline
- `output/` - generated videos and audio
