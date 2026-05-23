import cv2
import numpy as np
import streamlit as st
from websocket import create_connection
from streamlit_webrtc import webrtc_streamer, WebRtcMode


st.set_page_config(page_title="GestureVision Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /*  background o */
        .stApp {
            background-color: #0d0e12;
            color: #e0e6ed;
            font-family: 'Courier New', Courier, monospace;
        }

        /*  green borders and glow  */
        h1 {
            color: #00ffcc !important;
            text-shadow: 0 0 10px rgba(0,255,204,0.6);
            font-weight: 800;
            letter-spacing: 2px;
            border-bottom: 2px solid #00ffcc;
            padding-bottom: 10px;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #131722;
            border-right: 1px solid #1f293d;
        }

        /* Heads-up panels */
        .hud-card {
            background: rgba(20, 26, 40, 0.8);
            border: 1px solid #00ffcc;
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .hud-header {
            color: #ffaa00;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.95rem;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)


st.title(" CENTRAL CONSOLE")

col_video, col_hud = st.columns([7, 3])

st.sidebar.markdown("<h2 style='color:#ff007f; text-shadow: 0 0 8px rgba(255,0,127,0.5);'>GestureVision</h2>",
                    unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown("###  Matrix Controls")
brush_color = st.sidebar.color_picker(" Color", "#00ffcc")
sensitivity = st.sidebar.slider("Tracking  Level", 0.0, 100.0, 75.0)

st.sidebar.button("System Override (Reset)", use_container_width=True)

#(backend inqtegration)
NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"

if "vision_ws" not in globals():
    global vision_ws
    try:
        vision_ws = create_connection(NGROK_URL)
        st.sidebar.success(" NET PIPELINE LINKED")
    except Exception:
        st.sidebar.error("⚠️ SEARCHING FOR BACKEND MATRIX LINK...")
        vision_ws = None

def video_frame_callback(frame):
    global vision_ws
    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)

    img_resized = cv2.resize(img, (480, 360))

    if vision_ws is not None:
        try:
            _, jpeg_buffer = cv2.imencode('.jpg', img_resized,[int(cv2.IMWRITE_JPEG_QUALITY), 50])
            vision_ws.send_binary(jpeg_buffer.tobytes())

            processed_bytes = vision_ws.recv()
            nparr = np.frombuffer(processed_bytes, np.uint8)
            filtered_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if filtered_img is not None:
                final_render = cv2.resize(filtered_img, (img.shape[1], img.shape[0]))
                return frame.from_ndarray(final_render, format="bgr24")

        except Exception:
            pass

    return frame.from_ndarray(img, format="bgr24")

with col_video:
    st.markdown("### LIVE ROI ")
    webrtc_streamer(
        key="gesture-vision-hud",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col_hud:
    st.markdown("### DATA")
    st.markdown("""
        <div class="hud-card">
            <div class="hud-header"> OPERATIONAL GESTURE MAP</div>
            <p style="margin:5px 0; font-size:0.9rem;">👉 <b>Left Pinch</b> &nbsp; ➔ Cycle Next Filter</p>
            <p style="margin:5px 0; font-size:0.9rem;">👉 <b>Right Pinch</b> ➔ Cycle Prev Filter</p>
        </div>

        <div class="hud-card">
            <div class="hud-header"> HARDWARE STATS</div>
            <p style="margin:5px 0; font-size:0.85rem; color:#00ffcc;">• LATENCY: 24.81 ms/s</p>
            <p style="margin:5px 0; font-size:0.85rem; color:#00ffcc;">• DROP RATE: 0.00%</p>
            <p style="margin:5px 0; font-size:0.85rem; color:#00ffcc;">• DECODE RATIO: 39.3 m/s</p>
        </div>

        <div class="hud-card">
            <div class="hud-header"> NODE PIPELINE ENVIRONMENT</div>
            <p style="margin:0; font-size:0.85rem; color:#8892b0;">Engine Status: ACTIVE <br> Core Framework: Python / FastAPI<br> Vision Layer: OpenCV Matrix</p>
        </div>
    """, unsafe_allow_html=True)