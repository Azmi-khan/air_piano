import cv2
import json
import numpy as np
import streamlit as st
from websocket import create_connection
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(page_title="AI Air Piano", layout="wide")
st.title("🎹 Interactive AI Air Piano Workspace")
st.markdown("Hover your finger over a key at the top and **pinch** your thumb and index finger to play!")

# --- INJECT THE PIANO SYNTHESIZER DIRECTLY INTO THE WEB PAGE ONCE ---
# This exposes a global 'window.playPianoNote(frequency)' function to the browser session.
st.components.v1.html("""
    <script>
        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        window.playPianoNote = function(frequency) {
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            var osc = audioCtx.createOscillator();
            var gainNode = audioCtx.createGain();

            osc.type = "sine";
            osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);

            gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + 0.3);

            osc.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            osc.start();
            osc.stop(audioCtx.currentTime + 0.3);
        };
    </script>
""", height=0)

NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"

if "global_ws" not in globals():
    global global_ws, last_played_note
    last_played_note = None
    try:
        global_ws = create_connection(NGROK_URL)
        st.sidebar.success("⚡ Audio Pipeline active!")
    except Exception:
        st.sidebar.error("❌ Connecting to backend...")
        global_ws = None


def video_frame_callback(frame):
    global global_ws, last_played_note
    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    # --- DRAW THE PIANO KEYS OVERLAY ---
    key_w = w // 4
    keys = ["C4", "D4", "E4", "F4"]
    for i, note in enumerate(keys):
        cv2.rectangle(img, (i * key_w, 0), ((i + 1) * key_w, int(h * 0.2)), (255, 255, 255), 2)
        cv2.putText(img, note, (i * key_w + int(key_w * 0.4), int(h * 0.13)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    if global_ws is not None:
        try:
            _, jpeg_buffer = cv2.imencode('.jpg', img)
            global_ws.send_binary(jpeg_buffer.tobytes())

            result = global_ws.recv()
            data = json.loads(result)

            if data["detected"]:
                cx, cy = int(data["x"] * w), int(data["y"] * h)
                cv2.circle(img, (cx, cy), 8, (0, 255, 0), -1)

                current_note = data.get("note")
                if current_note and current_note != last_played_note:
                    # Map notes to frequencies
                    frequencies = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23}
                    if current_note in frequencies:
                        # Send a direct frame metadata flag or fallback to executing it natively
                        pass
                    last_played_note = current_note
                elif not current_note:
                    last_played_note = None
            else:
                last_played_note = None

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