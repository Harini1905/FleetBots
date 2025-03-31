from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import random
import time
import uuid
import asyncio
from typing import Dict, List, Set

app = FastAPI()
sessions = {}

# Store for WebSocket connections and historical data
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.data_history: Dict[str, List[dict]] = {}
        self.max_history_size = 100
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            self.data_history[session_id] = []
        self.active_connections[session_id].add(websocket)
        
        # Send historical data to new connections
        if self.data_history[session_id]:
            await websocket.send_json({
                "type": "history",
                "data": self.data_history[session_id]
            })
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                # Clean up empty sessions
                self.active_connections.pop(session_id, None)
    
    async def broadcast(self, message: dict, session_id: str):
        # Store in history
        if session_id not in self.data_history:
            self.data_history[session_id] = []
        
        self.data_history[session_id].append(message)
        
        # Maintain history size
        if len(self.data_history[session_id]) > self.max_history_size:
            self.data_history[session_id] = self.data_history[session_id][-self.max_history_size:]
        
        # Broadcast to all connections in the session
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json({
                        "type": "update",
                        "data": message
                    })
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[session_id].discard(conn)

manager = ConnectionManager()

def generate_sensor_data(rover_id):
    """Simulates rover sensor data"""
    return {
        "timestamp": time.time(),
        "rover_id": rover_id,
        "soil_moisture": round(random.uniform(20, 80), 2),
        "soil_pH": round(random.uniform(5.5, 7.5), 2),
        "temperature": round(random.uniform(10, 40), 2),
        "battery_level": round(random.uniform(10, 100), 2),
        "random_value": random.uniform(0, 100)  # Added random value as requested
    }

@app.post("/api/session/start")
def start_session():
    """Creates a new session with an isolated fleet"""
    session_id = str(uuid.uuid4())
    fleet_status = {f"Rover-{i}": {"status": "idle", "battery": random.randint(50, 100)} for i in range(1, 6)}
    sessions[session_id] = fleet_status
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls and WebSocket connections."}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Wait for any client messages
            data = await websocket.receive_text()
            # Process client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

# Background task to generate and broadcast data
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_periodic_data())

async def generate_periodic_data():
    while True:
        for session_id in list(sessions.keys()):
            for rover_id in sessions[session_id]:
                data = generate_sensor_data(rover_id)
                await manager.broadcast(data, session_id)
        
        # Wait for 1 second before next update
        await asyncio.sleep(1)

# REST API endpoints
@app.get("/api/fleet/status")
def get_fleet_status(session_id: str):
    """Returns the fleet status for a specific session"""
    return sessions.get(session_id, {"error": "Invalid session ID"})

@app.post("/api/rover/{rover_id}/reset")
def reset_rover(session_id: str, rover_id: str):
    """Resets the rover to idle state (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        sessions[session_id][rover_id]["status"] = "idle"
        return {"message": f"{rover_id} reset to idle"}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/status")
def get_rover_status(session_id: str, rover_id: str):
    """Returns status of a specific rover (per session)"""
    return sessions.get(session_id, {}).get(rover_id, {"error": "Rover not found"})

@app.post("/api/rover/{rover_id}/move")
def move_rover(session_id: str, rover_id: str, direction: str):
    """Moves the rover in a given direction (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        sessions[session_id][rover_id]["status"] = f"Moving {direction}"
        return {"message": f"{rover_id} moving {direction}"}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/battery")
def get_battery_level(session_id: str, rover_id: str):
    """Returns battery level of a specific rover (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        return {"rover_id": rover_id, "battery_level": sessions[session_id][rover_id]["battery"]}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/sensor-data")
def get_sensor_data(session_id: str, rover_id: str):
    """Fetch sensor data from a specific rover (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        return generate_sensor_data(rover_id)
    return {"error": "Invalid session or rover ID"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))  # Use Railway's assigned PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
