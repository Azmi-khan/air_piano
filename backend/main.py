import cv2
import json





from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app=FastAPI(title= "AI air piano - backend engine")

@app.get("/")
def home_check():
    """checking if the server is running"""
    return {"message": "german Server is running"}
@app.websocket("/ws/testing")
async def websocket_endpoint(websocket: WebSocket):
    """websocket test"""
    await websocket.accept()
    print("websocket accepted")

    try:
        while True:
            client_message = await websocket.receive_text()
            print(f"recieved {client_message}")
            await websocket.send_json({"server response": client_message})
    except WebSocketDisconnect:
        print("websocket disconnect")