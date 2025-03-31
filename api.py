@@ -1,73 +1,100 @@
 from fastapi import FastAPI
 import random
 import time
 import uuid

 
 app = FastAPI()
 
 
 sessions = {}
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
 
 @app.post("/api/session/start")
 def start_session():
     """Creates a new session with an isolated fleet"""
     session_id = str(uuid.uuid4())
     fleet_status = {f"Rover-{i}": {"status": "idle", "battery": random.randint(50, 100)} for i in range(1, 6)}
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
