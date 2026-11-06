# AI Video Generator

Simple local video generator using:
- OpenAI for prompt enhancement
- edge-tts for speech synthesis
- ffmpeg for video rendering

## Setup and Run

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OPENAI_API_KEY = "your_key_here"
.\.venv\Scripts\python.exe App.py --prompt "A cinematic drone shot over a futuristic city at sunrise"
```

## Files
- App.py - main generator
- output/ - generated videos
