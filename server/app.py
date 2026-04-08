# Copyright (c) 2026 WorkSim Voyager Team
# SPDX-License-Identifier: BSD-3-Clause
"""
FastAPI server for WorkSim Voyager.

Provides HTTP (/reset, /step, /state, /health, /schema) and a WebSocket
(/ws) endpoint — fully compatible with OpenEnv validation.
"""
from __future__ import annotations
import json, traceback
from typing import Any, Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from server.env import WorkSimVoyagerEnvironment

app = FastAPI(title="WorkSim Voyager", version="0.1.0",
              description="Workplace simulation OpenEnv environment")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html for root path
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# ── request / response models ─────────────────────────────────────────
class ResetRequest(BaseModel):
    seed: Optional[int] = None
    episode_id: Optional[str] = None
    task_id: Optional[str] = None

class StepRequest(BaseModel):
    action: Dict[str, Any] = Field(..., description="Action with tool, command, input")
    timeout_s: Optional[float] = None

# ── shared env instance (HTTP) ────────────────────────────────────────
_env = WorkSimVoyagerEnvironment()

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/reset")
async def reset(req: ResetRequest = ResetRequest()):
    return _env.reset(seed=req.seed, episode_id=req.episode_id, task_id=req.task_id)

@app.post("/step")
async def step(req: StepRequest):
    return _env.step(req.action)

@app.get("/state")
async def get_state():
    return _env.state()

@app.get("/schema")
async def get_schema():
    from server.models import WorkSimAction, WorkSimObservation
    return {
        "action": WorkSimAction.model_json_schema(),
        "observation": WorkSimObservation.model_json_schema(),
        "state": {"type": "object", "properties": {
            "episode_id": {"type": "string"}, "step_count": {"type": "integer"},
            "done": {"type": "boolean"}, "cumulative_reward": {"type": "number"}}},
    }

# ── WebSocket (per-session env) ──────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    env = WorkSimVoyagerEnvironment()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
                continue
            msg_type = msg.get("type", "")
            if msg_type == "reset":
                data = msg.get("data", {})
                result = env.reset(**data)
                await websocket.send_json({"type": "observation", "data": result})
            elif msg_type == "step":
                action = msg.get("data", {})
                result = env.step(action)
                await websocket.send_json({"type": "observation", "data": result})
            elif msg_type == "state":
                await websocket.send_json({"type": "state", "data": env.state()})
            elif msg_type == "close":
                await websocket.close()
                break
            else:
                await websocket.send_json({"type": "error",
                    "data": {"message": f"Unknown type: {msg_type}"}})
    except WebSocketDisconnect:
        pass
    except Exception:
        traceback.print_exc()

# ── CLI entry point ──────────────────────────────────────────────────
def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
