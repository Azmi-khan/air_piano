import cv2
import json
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(title= "AI air piano - backend engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # Allows traffic from any global network origin
    allow_credentials=True,
    allow_methods=["*"],             # Allows all global request types
    allow_headers=["*"],             # Allows all tracking headers
)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@app.get("/")
def home_check():
    """checking if the server is running"""
    return {"message": "german Server is running"}


@app.websocket("/ws/process")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🚀 Air Piano session connected!")

    try:
        while True:
            bytes_data = await websocket.receive_bytes()
            nparr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)


            response_data = {"detected": False, "x": 0, "y": 0, "note": None}

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                response_data["detected"] = True

                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

                response_data["x"] = index_tip.x
                response_data["y"] = index_tip.y


                distance = np.sqrt(
                    (index_tip.x - thumb_tip.x) ** 2 +
                    (index_tip.y - thumb_tip.y) ** 2 +
                    (index_tip.z - thumb_tip.z) ** 2
                )


                if distance < 0.06:

                    if index_tip.y < 0.20:
                        if 0.0 <= index_tip.x < 0.25:
                            response_data["note"] = "C4"
                        elif 0.25 <= index_tip.x < 0.50:
                            response_data["note"] = "D4"
                        elif 0.50 <= index_tip.x < 0.75:
                            response_data["note"] = "E4"
                        elif 0.75 <= index_tip.x <= 1.0:
                            response_data["note"] = "F4"

            await websocket.send_json(response_data)
    except WebSocketDisconnect:
        print("❌ Air Piano disconnected.")
    except Exception as e:
        print(f"Engine exception: {e}")