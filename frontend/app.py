import cv2
import json
import numpy as np
import streamlit as st
from websocket import create_connection

from streamlit_webrtc import webrtc_streamer, WebRtcMode

# Page Setup & Aesthetic Polish
st.set_page_config(page_title="AI Air Canvas", layout="wide")
st.title("🎨 Interactive AI Air Canvas")
st.markdown("Frontend: **Pakistan (Streamlit)** | Backend: **Germany (FastAPI)**")

# 1. Sidebar Panel Layout Configuration Elements
st.sidebar.header("Canvas Settings")
brush_color = st.sidebar.color_picker("Select Paint Color", "#FF0000")  # Defaults to Red
brush_thickness = st.sidebar.slider("Brush Thickness", 2, 20, 6)

# Translate hex color selector string layout to OpenCV BGR color layouts
hex_color = brush_color.lstrip('#')
bgr_color = tuple(int(hex_color[i:i + 2], 16) for i in (4, 2, 0))

# 2. Managing Shared Canvas Drawing State Memories
if "canvas" not in st.session_state:
    st.session_state.canvas = None
if "prev_point" not in st.session_state:
    st.session_state.prev_point = None

if st.sidebar.button("Clear Canvas", use_container_width=True):
    st.session_state.canvas = None
    st.session_state.prev_point = None
    st.rerun()

# 3. Setup Networking WebSocket Connection Address Links
# Paste your active running Ngrok WSS address directly in between these quotes!
NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"

if "ws_conn" not in st.session_state:
    try:
        st.session_state.ws_conn = create_connection(NGROK_URL)
        st.sidebar.success("⚡ Connected to Germany AI Backend!")
    except Exception as e:
        st.sidebar.error("❌ Awaiting connection to Germany Backend...")
        st.session_state.ws_conn = None


# 4. The Live Frame Capture Loop Callback
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)  # Natural mirrored visual effect
    h, w, _ = img.shape

    # Instantiate clean drawing board matrix layers if empty
    if st.session_state.canvas is None or st.session_state.canvas.shape != img.shape:
        st.session_state.canvas = np.zeros_like(img)

    # Stream frames over the socket connection network tunnel if active
    if st.session_state.ws_conn is not None:
        try:
            # Compress array matrix data configurations to lightweight JPEGs
            _, jpeg_buffer = cv2.imencode('.jpg', img)
            st.session_state.ws_conn.send_binary(jpeg_buffer.tobytes())

            # Catch incoming processed AI vector positions
            result = st.session_state.ws_conn.recv()
            data = json.loads(result)

            if data["detected"]:
                cx, cy = int(data["x"] * w), int(data["y"] * h)

                if data["drawing"]:
                    if st.session_state.prev_point is not None:
                        # Draw vector line stroke structures
                        cv2.line(st.session_state.canvas, st.session_state.prev_point, (cx, cy), bgr_color,
                                 brush_thickness)
                    st.session_state.prev_point = (cx, cy)
                else:
                    st.session_state.prev_point = None

                # Render a visual reticle circle at the current tracking pointer location
                cv2.circle(img, (cx, cy), 8, (0, 0, 255), -1)
            else:
                st.session_state.prev_point = None

        except Exception:
            pass

    # Blend original raw video and digital ink overlay layers together
    final_output = cv2.addWeighted(img, 1.0, st.session_state.canvas, 1.0, 0)
    return frame.from_ndarray(final_output, format="bgr24")


# 5. Native Browser WebRTC Hardware Hook Stream Renderers
webrtc_streamer(
    key="air-canvas-streamer",
    mode=WebRtcMode.VIDEORECVONLY,
    video_frame_callback=video_frame_callback,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)