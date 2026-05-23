import cv2
import json
import time
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GestureVision - Advanced HUD Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4
)

FILTERS = ["Normal", "Gray", "Sketch", "Invert", "Thermal"]
current_filter_idx = 0
cooldown_counter = 0


def apply_image_filter(img, filter_name):
    if img.size == 0:
        return img
    if filter_name == "Gray":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif filter_name == "Sketch":
        gray, color = cv2.pencilSketch(img, sigma_s=30, sigma_r=0.03, shade_factor=0.03)
        return color
    elif filter_name == "Invert":
        return cv2.bitwise_not(img)
    elif filter_name == "Thermal":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    return img


def draw_cyber_corners(img, x_min, y_min, x_max, y_max, color=(0, 255, 255), thickness=2, length=20):

    cv2.line(img, (x_min, y_min), (x_min + length, y_min), color, thickness)
    cv2.line(img, (x_min, y_min), (x_min, y_min + length), color, thickness)

    cv2.line(img, (x_max, y_min), (x_max - length, y_min), color, thickness)
    cv2.line(img, (x_max, y_min), (x_max, y_min + length), color, thickness)

    cv2.line(img, (x_min, y_max), (x_min + length, y_max), color, thickness)
    cv2.line(img, (x_min, y_max), (x_min, y_max - length), color, thickness)

    cv2.line(img, (x_max, y_max), (x_max - length, y_max), color, thickness)
    cv2.line(img, (x_max, y_max), (x_max, y_max - length), color, thickness)


@app.websocket("/ws/process")
async def websocket_endpoint(websocket: WebSocket):
    global current_filter_idx, cooldown_counter
    await websocket.accept()
    print(" Active!")

    try:
        while True:
            bytes_data = await websocket.receive_bytes()
            start_time = time.time()

            nparr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if cooldown_counter > 0:
                cooldown_counter -= 1

            left_index_pos = None
            right_index_pos = None
            display_frame = frame.copy()

            if results.multi_hand_landmarks and results.multi_handedness:
                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    hand_label = results.multi_handedness[idx].classification[0].label

                    mp_draw.draw_landmarks(
                        display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                        mp_draw.DrawingSpec(color=(0, 255, 204), thickness=1, circle_radius=1),
                        mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1)
                    )

                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    cx, cy = int(index_tip.x * w), int(index_tip.y * h)

                    if hand_label == "Left" or index_tip.x < 0.5:
                        left_index_pos = (cx, cy)
                    if hand_label == "Right" or index_tip.x >= 0.5:
                        right_index_pos = (cx, cy)

                    distance = np.sqrt((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2)
                    if distance < 0.04 and cooldown_counter == 0:
                        if hand_label == "Left":
                            current_filter_idx = (current_filter_idx + 1) % len(FILTERS)
                        elif hand_label == "Right":
                            current_filter_idx = (current_filter_idx - 1) % len(FILTERS)
                        cooldown_counter = 8
                        break

            active_filter = FILTERS[current_filter_idx]

            if left_index_pos and right_index_pos:
                x_min = max(0, min(left_index_pos[0], right_index_pos[0]))
                x_max = min(w, max(left_index_pos[0], right_index_pos[0]))
                y_min = max(0, min(left_index_pos[1], right_index_pos[1]))
                y_max = min(h, max(left_index_pos[1], right_index_pos[1]))

                if (x_max - x_min) > 15 and (y_max - y_min) > 15:
                    roi = frame[y_min:y_max, x_min:x_max]
                    filtered_roi = apply_image_filter(roi, active_filter)


                    display_frame[y_min:y_max, x_min:x_max] = filtered_roi

                    draw_cyber_corners(display_frame, x_min, y_min, x_max, y_max, color=(0, 242, 255), thickness=3,
                                       length=25)
                    cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), (0, 242, 255), 1)

                    cv2.putText(display_frame, f"ACTIVE ROI FILTER: {active_filter.upper()}", (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 242, 255), 1, cv2.LINE_AA)

            latency = (time.time() - start_time) * 1000

            cv2.rectangle(display_frame, (15, 15), (380, 85), (20, 16, 12), -1)
            cv2.rectangle(display_frame, (15, 15), (380, 85), (0, 255, 204), 1)

            cv2.putText(display_frame, f"GESTUREVISION PRO | MODE: {active_filter.upper()}", (25, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 204), 1, cv2.LINE_AA)
            cv2.putText(display_frame, f"• NET LATENCY: {latency:.2f} ms", (25, 56),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (224, 230, 237), 1, cv2.LINE_AA)
            cv2.putText(display_frame, f"• PIPELINE FLOW: ACTIVE", (25, 72),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (224, 230, 237), 1, cv2.LINE_AA)

            _, encoded_buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            await websocket.send_bytes(encoded_buffer.tobytes())

    except WebSocketDisconnect:
        print("❌ Session dropped clean.")