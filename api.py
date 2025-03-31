from fastapi import FastAPI
import random
import time
import os
from threading import Lock

app = FastAPI()
lock = Lock()

# Persistent storage for rover state
rover = {
    "timestamp": time.time(),
    "position": {"x": round(random.uniform(0, 100), 2), "y": round(random.uniform(0, 100), 2)},
    "ultrasonic_distance": round(random.uniform(1.0, 5.0), 2),
    "ir_signal_strength": 0.0,
    "rfid_detected": False,
    "accelerometer": {"x": 0.0, "y": 0.0, "z": 0.0},
    "battery_level": 100.0,
    "communication_status": "Connected",
    "recharging": False
}

movement_commands = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

def update_rover_data():
    """Update rover data realistically over time."""
    with lock:
        rover["timestamp"] = time.time()
        
        # Simulate ultrasonic sensor detecting obstacles
        rover["ultrasonic_distance"] = max(0.3, min(5.0, rover["ultrasonic_distance"] + round(random.uniform(-0.5, 0.5), 2)))
        
        # IR signal increases if near a survivor (random event)
        if random.random() < 0.1:
            rover["ir_signal_strength"] = round(random.uniform(50, 100), 2)
            rover["rfid_detected"] = random.choice([True, False])
        else:
            rover["ir_signal_strength"] = max(0, rover["ir_signal_strength"] - 5)
            rover["rfid_detected"] = False
        
        # Simulate rough terrain affecting accelerometer readings
        rover["accelerometer"] = {
            "x": round(random.uniform(-0.2, 0.2), 2),
            "y": round(random.uniform(-0.2, 0.2), 2),
            "z": round(random.uniform(-0.2, 0.2), 2)
        }
        
        # Battery drains realistically
        if not rover["recharging"]:
            rover["battery_level"] = max(0, rover["battery_level"] - round(random.uniform(0.1, 1.0), 2))
        
        # If battery is critically low, start recharging
        if rover["battery_level"] <= 5:
            rover["recharging"] = True
        
        # If recharging, slowly restore battery level
        if rover["recharging"]:
            rover["battery_level"] = min(80, rover["battery_level"] + round(random.uniform(1.0, 3.0), 2))
            if rover["battery_level"] >= 80:
                rover["recharging"] = False
        
        # Communication status changes based on battery & randomness
        if rover["battery_level"] < 10:
            rover["communication_status"] = "Lost"
        else:
            rover["communication_status"] = random.choice(["Connected", "Intermittent", "Lost"])
    
    return rover

@app.get("/")
def read_root():
    return {"message": "Disaster Rover API is running!"}

@app.get("/api/disaster-rover-data")
def get_rover_data():
    """Fetch realistic rover sensor data"""
    return update_rover_data()

@app.post("/api/move/{direction}")
def move_rover(direction: str):
    """Move the rover based on the given direction (forward, backward, left, right)"""
    if direction not in movement_commands:
        return {"error": "Invalid movement command. Use forward, backward, left, or right."}
    
    with lock:
        dx, dy = movement_commands[direction]
        rover["position"]["x"] = round(rover["position"]["x"] + dx, 2)
        rover["position"]["y"] = round(rover["position"]["y"] + dy, 2)
    
    return {"message": f"Rover moved {direction}", "new_position": rover["position"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
