import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(page_title="AI Air Piano Workspace", layout="wide")
st.title("🎹 Live AI Air Piano Console")
st.markdown("### Hand-Tracking Musical Canvas")

# UPDATE THIS TO YOUR CURRENT SECURE NGROK LINK BEFORE PUSHING TO GITHUB!
NGROK_URL = "wss://unknowing-goatskin-herring.ngrok-free.dev/ws/process"

# --- THE JAVASCRIPT WEBRTC + AUDIO NETWORKING BRIDGE ---
# This runs completely inside her web browser, bypassing the Linux server limits entirely!
st.components.v1.html(f"""
    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; color: white; margin-bottom: 20px;">
        <h4 style="margin: 0 0 10px 0;">🎙️ Status: <span id="status" style="color: #ffaa00;">Initializing Audio Pipeline...</span></h4>
    </div>

    <script>
        var statusEl = document.getElementById("status");
        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        var ws = new WebSocket("{NGROK_URL}");

        var NOTE_FREQS = {{"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23}};
        var lastNote = null;

        ws.onopen = function() {{
            statusEl.innerText = "⚡ Connected to Germany Engine! Click START below.";
            statusEl.style.color = "#00ff00";
        }};

        ws.onerror = function() {{
            statusEl.innerText = "❌ Offline. Awaiting backend deployment link...";
            statusEl.style.color = "#ff0000";
        }};

        // Global Synth Engine
        function playNote(freq) {{
            if (audioCtx.state === 'suspended') {{
                audioCtx.resume();
            }}
            var osc = audioCtx.createOscillator();
            var gainNode = audioCtx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + 0.3);
            osc.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.3);
        }}

        // Listen for tracking frame coordinate returns from your backend
        ws.onmessage = function(event) {{
            var data = JSON.parse(event.data);
            if (data.detected && data.note) {{
                if (data.note !== lastNote) {{
                    var freq = NOTE_FREQS[data.note];
                    if (freq) playNote(freq);
                    lastNote = data.note;
                }}
            }} else {{
                lastNote = null;
            }}
        }};

        // Intercept WebRTC browser video tracks to pump raw canvas frames down the socket channel
        navigator.mediaDevices.getUserMedia({{ video: true, audio: false }})
            .then(function(stream) {{
                var videoTrack = stream.getVideoTracks()[0];
                var imageCapture = new ImageCapture(videoTrack);

                // Stream loops at 25 FPS natively inside her browser frame
                setInterval(function() {{
                    if (ws.readyState === WebSocket.OPEN) {{
                        imageCapture.grabFrame()
                            .then(function(imageBitmap) {{
                                var canvas = document.createElement("canvas");
                                canvas.width = imageBitmap.width;
                                canvas.height = imageBitmap.height;
                                var ctx = canvas.getContext("2d");
                                ctx.drawImage(imageBitmap, 0, 0);
                                canvas.toBlob(function(blob) {{
                                    ws.send(blob);
                                }}, "image/jpeg", 0.7);
                            }})
                            .catch(function(err) {{ }});
                    }}
                }}, 40);
            }});
    </script>
""", height=100)

# --- THE UNIVERSAL STREAMLIT CLOUD HARDWARE CONTEXT WRAPPER ---
# Includes public STUN configurations so your girlfriend can open this safely from any Wi-Fi network or data plan
webrtc_streamer(
    key="air-piano-streamer",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}]
    },
    async_processing=True,
)