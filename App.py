import argparse
import asyncio
import math
import os
import subprocess
import textwrap
import wave
from pathlib import Path

import edge_tts
import numpy as np
from imageio_ffmpeg import get_ffmpeg_exe
from openai import OpenAI


DEFAULT_VOICE = "en-US-JennyNeural"


def build_prompt_script(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return prompt

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Turn the user's prompt into a short cinematic narration script under 120 words.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=180,
        )
        text = response.choices[0].message.content.strip()
        if text:
            return text
    except Exception:
        pass
    return prompt


def wrap_text(text: str, width: int = 36) -> str:
    wrapped = textwrap.wrap(text, width=width)
    return "\n".join(wrapped[:4])


def generate_fallback_audio(filename: Path, duration_seconds: float = 12.0, sample_rate: int = 22050) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    total_samples = int(sample_rate * duration_seconds)
    t = np.linspace(0, duration_seconds, total_samples, endpoint=False)
    tone = 0.4 * np.sin(2 * math.pi * 220 * t) + 0.3 * np.sin(2 * math.pi * 330 * t)
    pcm = np.int16(tone * 32767)

    with wave.open(str(filename), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


async def synthesize_voiceover(text: str, filename: Path, voice: str = DEFAULT_VOICE) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice)
    try:
        await asyncio.wait_for(communicate.save(str(filename)), timeout=20)
    except Exception:
        generate_fallback_audio(filename, duration_seconds=max(8.0, min(18.0, len(text.split()) * 0.55)))


def assemble_video(prompt: str, audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(6.0, min(22.0, len(prompt.split()) * 0.6))

    audio_input = str(audio_path.resolve())
    output_target = str(output_path.resolve())
    ffmpeg_exe = get_ffmpeg_exe()
    command = [
        ffmpeg_exe,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x1f2937:s=1280x720:d={duration}",
        "-i",
        audio_input,
        "-shortest",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_target,
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Video created: {output_target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a short AI video from a prompt.")
    parser.add_argument("--prompt", required=True, help="Prompt to turn into a video.")
    parser.add_argument("--output", default="output/final_video.mp4", help="Output path for the generated video.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="TTS voice name to use.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    script = build_prompt_script(args.prompt)
    audio_path = output_path.with_suffix(".mp3")
    await synthesize_voiceover(script, audio_path, voice=args.voice)
    assemble_video(script, audio_path, output_path)


if __name__ == "__main__":
    asyncio.run(main())
