from fastapi import FastAPI
import random
import time
import uuid
import threading

app = FastAPI()

sessions = {}

# Movement deltas for coordinate updates
MOVEMENT_DELTAS = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

def generate_sensor_data(rover_id):
    """Simulates rover sensor data"""
    return {
        "timestamp": time.time(),
        "rover_id": rover_id,
        "soil_moisture": round(random.uniform(20, 80), 2),
        "soil_pH": round(random.uniform(5.5, 7.5), 2),
        "temperature": round(random.uniform(10, 40), 2),
        "battery_level": round(random.uniform(10, 100), 2)
    }

def move_rover_continuously(session_id, rover_id, direction):
    """Moves the rover continuously in the given direction over time"""
    while sessions[session_id][rover_id]["status"] == f"Moving {direction}":
        dx, dy = MOVEMENT_DELTAS[direction]
        x, y = sessions[session_id][rover_id]["coordinates"]
        sessions[session_id][rover_id]["coordinates"] = (x + dx, y + dy)
        time.sleep(1)  # Increment position every second

@app.post("/api/session/start")
def start_session():
    """Creates a new session with an isolated fleet"""
    session_id = str(uuid.uuid4())
    fleet_status = {
        f"Rover-{i}": {"status": "idle", "battery": random.randint(50, 100), "coordinates": (0, 0)}
        for i in range(1, 6)
    }
    sessions[session_id] = fleet_status
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls."}

@app.get("/api/fleet/status")
def get_fleet_status(session_id: str):
    """Returns the fleet status for a specific session"""
    return sessions.get(session_id, {"error": "Invalid session ID"})

@app.post("/api/rover/{rover_id}/reset")
def reset_rover(session_id: str, rover_id: str):
    """Resets the rover to idle state (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        sessions[session_id][rover_id]["status"] = "idle"
        sessions[session_id][rover_id]["coordinates"] = (0, 0)
        return {"message": f"{rover_id} reset to idle and coordinates set to (0,0)"}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/status")
def get_rover_status(session_id: str, rover_id: str):
    """Returns status of a specific rover (per session)"""
    return sessions.get(session_id, {}).get(rover_id, {"error": "Rover not found"})

@app.post("/api/rover/{rover_id}/move")
def move_rover(session_id: str, rover_id: str, direction: str):
    """Moves the rover in a given direction (per session) and updates coordinates incrementally"""
    if session_id in sessions and rover_id in sessions[session_id]:
        if direction not in MOVEMENT_DELTAS:
            return {"error": "Invalid direction. Use forward, backward, left, or right."}
        
        sessions[session_id][rover_id]["status"] = f"Moving {direction}"
        threading.Thread(target=move_rover_continuously, args=(session_id, rover_id, direction), daemon=True).start()
        return {"message": f"{rover_id} started moving {direction}"}
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

@app.get("/api/rover/{rover_id}/coordinates")
def get_rover_coordinates(session_id: str, rover_id: str):
    """Returns the current coordinates of the rover"""
    if session_id in sessions and rover_id in sessions[session_id]:
        return {"rover_id": rover_id, "coordinates": sessions[session_id][rover_id]["coordinates"]}
    return {"error": "Invalid session or rover ID"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))  # Use Railway's assigned PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
