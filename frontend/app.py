import cv2
import json
import numpy as np
import streamlit as st
from websocket import create_connection
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# --- TEST PLATFORM FOR WINSOUND Safely ---
# This prevents the Linux cloud server from crashing on boot!
try:
    import winsound

    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

st.set_page_config(page_title="AI Air Piano", layout="wide")
st.title("🎹 Interactive AI Air Piano Workspace")
st.markdown("Hover your finger over a key at the top and **pinch** your thumb and index finger to play!")

NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"

if "piano_ws" not in globals():
    global piano_ws, last_note
    last_note = None
    try:
        piano_ws = create_connection(NGROK_URL)
        st.sidebar.success("⚡ Audio Pipeline Connected globally!")
    except Exception as e:
        st.sidebar.error("❌ Connecting to backend...")
        piano_ws = None

NOTE_FREQS = {"C4": 261, "D4": 294, "E4": 330, "F4": 349}


def video_frame_callback(frame):
    global piano_ws, last_note

    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    # --- DRAW THE PIANO KEYS VISUAL OVERLAY ---
    key_w = w // 4
    keys = ["C4", "D4", "E4", "F4"]
    for i, note in enumerate(keys):
        cv2.rectangle(img, (i * key_w, 0), ((i + 1) * key_w, int(h * 0.2)), (255, 255, 255), 2)
        cv2.putText(img, note, (i * key_w + int(key_w * 0.4), int(h * 0.13)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    if piano_ws is not None:
        try:
            _, jpeg_buffer = cv2.imencode('.jpg', img)
            piano_ws.send_binary(jpeg_buffer.tobytes())

            result = piano_ws.recv()
            data = json.loads(result)

            if data["detected"]:
                cx, cy = int(data["x"] * w), int(data["y"] * h)
                cv2.circle(img, (cx, cy), 8, (0, 255, 0), -1)

                detected_note = data.get("note")
                if detected_note and detected_note != last_note:
                    freq = NOTE_FREQS.get(detected_note)
                    if freq:
                        # If running locally on Windows, use system hardware beep
                        if IS_WINDOWS:
                            winsound.Beep(freq, 150)
                        else:
                            # Natively triggers a clean standard terminal ring sound on Linux cloud hosts
                            print('\a', end='', flush=True)

                    last_note = detected_note
                elif not detected_note:
                    last_note = None
            else:
                last_note = None

        except Exception:
            pass

    return frame.from_ndarray(img, format="bgr24")


webrtc_streamer(
    key="air-piano-streamer",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_frame_callback,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)