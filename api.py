from fastapi import FastAPI
import random
import time

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Slambot Fleet API is running!"}

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

fleet_status = {f"Rover-{i}": {"status": "idle", "battery": random.randint(50, 100)} for i in range(1, 6)}

@app.get("/api/fleet/status")
def get_fleet_status():
    """Returns the status of all rovers"""
    return fleet_status

@app.get("/api/rover/{rover_id}/status")
def get_rover_status(rover_id: str):
    """Returns status of a specific rover"""
    return fleet_status.get(rover_id, {"error": "Rover not found"})

@app.post("/api/rover/{rover_id}/move")
def move_rover(rover_id: str, direction: str):
    """Moves the rover in a given direction"""
    if rover_id in fleet_status:
        fleet_status[rover_id]["status"] = f"Moving {direction}"
        return {"message": f"{rover_id} moving {direction}"}
    return {"error": "Rover not found"}

@app.get("/api/rover/{rover_id}/battery")
def get_battery_level(rover_id: str):
    """Returns battery level of a specific rover"""
    if rover_id in fleet_status:
        return {"rover_id": rover_id, "battery_level": fleet_status[rover_id]["battery"]}
    return {"error": "Rover not found"}

@app.get("/api/rover/{rover_id}/sensor-data")
def get_sensor_data(rover_id: str):
    """Fetch sensor data from a specific rover"""
    if rover_id in fleet_status:
        return generate_sensor_data(rover_id)
    return {"error": "Rover not found"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))  # Use Railway's assigned PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
