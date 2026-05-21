import cv2
import mediapipe as mp
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

# Set up clean web page configuration
st.set_page_config(page_title="AI Hand Tracker", layout="wide")

st.title("🤖 Real-Time AI Hand Tracker")
st.markdown("Welcome to your first Computer Vision web app! Allow webcam access below to see the tracking in action.")

# Sidebar controls for user interaction
st.sidebar.header("Control Panel")
max_hands = st.sidebar.slider("Maximum Hands to Track", min_value=1, max_value=4, value=2)
detection_confidence = st.sidebar.slider("Detection Confidence", min_value=0.0, max_value=1.0, value=0.7, step=0.05)

# Initialize MediaPipe components globally for drawing
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


# This core function processes the video frame-by-frame inside the browser stream
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    # Mirror effect
    img = cv2.flip(img, 1)

    # Initialize the model INSIDE the frame processing or globally.
    # Note: For best practice with dynamic sliders in webrtc, we spin it up inside the context
    # or keep it persistent. To keep it simple and reactive to your sidebar sliders:
    with mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=0.7
    ) as hands:

        # Convert color spaces for AI engine
        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # If landmarks are found, overlay the skeleton map
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    img,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

    return frame.from_ndarray(img, format="bgr24")


# Layout separation using columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live WebRTC Video Stream")
    # CHANGED: mode shifted to SENDRECV so it asks for your webcam permission
    webrtc_streamer(
        key="hand-pose-detection",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col2:
    st.subheader("System Status")
    st.info("The AI engine is ready. Adjust the sidebar parameters to change confidence scaling on the fly.")
    st.markdown("""
    ### How to test:
    1. Click the **Start** button in the video player.
    2. Grant your browser permission to use your camera.
    3. Hold up your hands!
    """)