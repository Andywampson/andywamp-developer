import subprocess
import sys
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = APP_DIR / "output" / "final_video.mp4"
VOICES = ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]

st.set_page_config(page_title="AI Video Generator", page_icon="🎬", layout="centered")
st.title("AI Video Generator")
st.caption("Turn a concept into a short narrated video.")
st.info("OpenAI script enhancement is optional. Without an API key, your prompt is used as the narration.")

with st.form("video_generator"):
    user_prompt = st.text_area(
        "Video concept",
        value="A cinematic drone shot over a futuristic city at sunrise",
        max_chars=1000,
        height=120,
        placeholder="Describe the video you want to create",
    )
    voice = st.selectbox("Narration voice", VOICES)
    submitted = st.form_submit_button("Generate video", type="primary", width="stretch")

if submitted:
    st.session_state.pop("generated_video", None)
    if not user_prompt.strip():
        st.error("Enter a video concept first.")
    else:
        command = [
            sys.executable,
            str(APP_DIR / "App.py"),
            "--prompt",
            user_prompt.strip(),
            "--voice",
            voice,
            "--output",
            str(OUTPUT_PATH),
        ]
        try:
            with st.spinner("Creating your narrated video..."):
                result = subprocess.run(
                    command,
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            st.error("Video generation timed out. Try a shorter prompt and run it again.")
        else:
            if result.returncode != 0:
                st.error("Video generation failed.")
                if result.stderr.strip():
                    st.code(result.stderr[-4000:])
            elif not OUTPUT_PATH.is_file():
                st.error("The generator finished without creating an MP4 file.")
            else:
                st.session_state["generated_video"] = str(OUTPUT_PATH)
                st.success("Your video is ready.")

video_path = st.session_state.get("generated_video")
if video_path and Path(video_path).is_file():
    video_file = Path(video_path)
    st.subheader("Preview")
    st.video(str(video_file))
    st.download_button(
        "Download MP4",
        data=video_file.read_bytes(),
        file_name="ai-video.mp4",
        mime="video/mp4",
        width="stretch",
    )
