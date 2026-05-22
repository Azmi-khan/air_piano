import cv2
import json
import numpy as np
import streamlit as st
from websocket import create_connection
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(page_title="AI Air Canvas", layout="wide")
st.title("Interactive AI Air Canvas")
st.markdown("Frontend: ** Streamlit **| Backend: ** FastAPI**")


st.sidebar.header("Canvas Settings")
brush_color = st.sidebar.color_picker("Select Paint Color", "#FF0000")
brush_thickness = st.sidebar.slider("Brush Thickness", 2, 20, 6)


hex_color = brush_color.lstrip('#')
bgr_color = tuple(int(hex_color[i:i + 2], 16) for i in (4, 2, 0))


NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"


if "canvas_matrix" not in globals():
    global canvas_matrix, prev_point, global_ws
    canvas_matrix = None
    prev_point = None
    try:
        global_ws = create_connection(NGROK_URL)
        st.sidebar.success("⚡ Connected to AI Backend!")
    except Exception as e:
        st.sidebar.error("❌ Awaiting connection to  Backend...")
        global_ws = None

if st.sidebar.button("Clear Canvas", use_container_width=True):
    canvas_matrix = None
    prev_point = None
    st.rerun()



def video_frame_callback(frame):
    global canvas_matrix, prev_point, global_ws

    img = frame.to_ndarray(format="bgr24")
    img = cv2.flip(img, 1)
    h, w, _ = img.shape


    if canvas_matrix is None or canvas_matrix.shape != img.shape:
        canvas_matrix = np.zeros_like(img)


    if global_ws is not None:
        try:

            _, jpeg_buffer = cv2.imencode('.jpg', img)
            global_ws.send_binary(jpeg_buffer.tobytes())


            result = global_ws.recv()
            data = json.loads(result)

            if data["detected"]:
                cx, cy = int(data["x"] * w), int(data["y"] * h)

                if data["drawing"]:
                    if prev_point is not None:

                        cv2.line(canvas_matrix, prev_point, (cx, cy), bgr_color, brush_thickness)
                    prev_point = (cx, cy)
                else:
                    prev_point = None


                cv2.circle(img, (cx, cy), 8, (0, 0, 255), -1)
            else:
                prev_point = None

        except Exception as e:
            print(f"Tracking frame drop or socket skip: {e}")
            pass


    final_output = cv2.addWeighted(img, 1.0, canvas_matrix, 1.0, 0)
    return frame.from_ndarray(final_output, format="bgr24")


webrtc_streamer(
    key="air-canvas-streamer",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_frame_callback,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)