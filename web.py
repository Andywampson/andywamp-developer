import subprocess
import sys
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = APP_DIR / "output" / "final_video.mp4"
VOICES = ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]
IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_COUNT = 5
MAX_IMAGE_SIZE = 15 * 1024 * 1024

st.set_page_config(page_title="AI Video Generator", page_icon="🎬", layout="centered")
st.title("AI Video Generator")
st.caption("Create a short narrated video from your concept and photos.")
st.info("OpenAI receives only the prompt when script enhancement is enabled. Photos are used by the local renderer only.")

with st.form("video_generator"):
    user_prompt = st.text_area(
        "Video concept",
        value="A cinematic drone shot over a futuristic city at sunrise",
        max_chars=1000,
        height=120,
        placeholder="Describe the video you want to create",
    )
    voice = st.selectbox("Narration voice", VOICES)
    uploaded_images = st.file_uploader(
        "Scene photos",
        type=IMAGE_TYPES,
        accept_multiple_files=True,
        help="Optional: add up to five JPG, PNG, or WebP images. Each image must be 15 MB or smaller.",
    )
    submitted = st.form_submit_button("Generate video", type="primary", width="stretch")

if submitted:
    st.session_state.pop("generated_video", None)
    if not user_prompt.strip():
        st.error("Enter a video concept first.")
    elif len(uploaded_images) > MAX_IMAGE_COUNT:
        st.error(f"Upload no more than {MAX_IMAGE_COUNT} scene photos.")
    elif any(image.size > MAX_IMAGE_SIZE for image in uploaded_images):
        st.error("Each scene photo must be 15 MB or smaller.")
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
            with tempfile.TemporaryDirectory(prefix="ai-video-scenes-") as temp_dir:
                for index, uploaded_image in enumerate(uploaded_images):
                    extension = Path(uploaded_image.name).suffix.lower()
                    image_path = Path(temp_dir) / f"scene_{index}{extension}"
                    image_path.write_bytes(uploaded_image.getvalue())
                    command.extend(["--image", str(image_path)])

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
