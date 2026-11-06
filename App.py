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


async def synthesize_voiceover(text: str, filename: Path, voice: str = DEFAULT_VOICE) -> bool:
    filename.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice)
    try:
        await asyncio.wait_for(communicate.save(str(filename)), timeout=20)
        return True
    except Exception:
        generate_fallback_audio(filename, duration_seconds=max(8.0, min(18.0, len(text.split()) * 0.55)))
        return False


def assemble_video(
    prompt: str,
    audio_path: Path,
    output_path: Path,
    image_paths: list[Path] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(6.0, min(22.0, len(prompt.split()) * 0.6))

    audio_input = str(audio_path.resolve())
    output_target = str(output_path.resolve())
    ffmpeg_exe = get_ffmpeg_exe()
    image_paths = image_paths or []
    if len(image_paths) > 5:
        raise ValueError("Use at most five scene images.")
    missing_images = [path for path in image_paths if not path.is_file()]
    if missing_images:
        raise FileNotFoundError(f"Scene image not found: {missing_images[0]}")

    command = [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error"]
    if image_paths:
        scene_duration = duration / len(image_paths)
        filters = []
        for index, image_path in enumerate(image_paths):
            command.extend(
                [
                    "-loop",
                    "1",
                    "-framerate",
                    "30",
                    "-t",
                    f"{scene_duration:.3f}",
                    "-i",
                    str(image_path.resolve()),
                ]
            )
            filters.append(
                f"[{index}:v]scale=1280:720:force_original_aspect_ratio=increase,"
                f"crop=1280:720,setsar=1,"
                f"zoompan=z='min(zoom+0.0005,1.08)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=30,"
                f"trim=duration={scene_duration:.3f},setpts=PTS-STARTPTS[v{index}]"
            )

        audio_index = len(image_paths)
        command.extend(["-i", audio_input])
        scene_inputs = "".join(f"[v{index}]" for index in range(len(image_paths)))
        filters.append(f"{scene_inputs}concat=n={len(image_paths)}:v=1:a=0[vout]")
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[vout]",
                "-map",
                f"{audio_index}:a:0",
            ]
        )
    else:
        command.extend(
            [
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x1f2937:s=1280x720:d={duration}",
                "-i",
                audio_input,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
            ]
        )

    command.extend(
        [
            "-shortest",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            output_target,
        ]
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:] or "FFmpeg could not assemble the video.")
    print(f"Video created: {output_target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a short AI video from a prompt.")
    parser.add_argument("--prompt", required=True, help="Prompt to turn into a video.")
    parser.add_argument("--output", default="output/final_video.mp4", help="Output path for the generated video.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="TTS voice name to use.")
    parser.add_argument(
        "--image",
        action="append",
        type=Path,
        default=[],
        help="Scene image path; repeat the option to add up to five images.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if not args.prompt.strip():
        raise SystemExit("Prompt must not be empty.")
    if len(args.image) > 5:
        raise SystemExit("Use at most five scene images.")
    for image_path in args.image:
        if not image_path.is_file():
            raise SystemExit(f"Scene image not found: {image_path}")
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise SystemExit(f"Unsupported scene image format: {image_path.suffix}")

    output_path = Path(args.output)
    script = build_prompt_script(args.prompt)
    audio_path = output_path.with_suffix(".mp3")
    has_voiceover = await synthesize_voiceover(script, audio_path, voice=args.voice)
    assemble_video(script, audio_path, output_path, image_paths=args.image)
    if not has_voiceover:
        print("VOICEOVER_FALLBACK: speech service unavailable; generated audio is a tone.")


if __name__ == "__main__":
    asyncio.run(main())
